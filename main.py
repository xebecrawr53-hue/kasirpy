from flask import Flask, render_template, jsonify, request, make_response
import datetime
import random
import string
import os
import json
import csv
import io
from collections import Counter
from supabase import create_client, Client

app = Flask(__name__)

# Supabase Configuration
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")
supabase: Client = create_client(url, key)

UNAVAILABLE_ITEMS_FILE = "unavailable_items.json"

def get_unavailable_ids():
    if not os.path.exists(UNAVAILABLE_ITEMS_FILE):
        return []
    try:
        with open(UNAVAILABLE_ITEMS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_unavailable_ids(ids):
    with open(UNAVAILABLE_ITEMS_FILE, "w") as f:
        json.dump(ids, f)

def calculate_analytics():
    try:
        response = supabase.table('transactions').select("*").execute()
        all_txns = response.data or []
    except Exception as e:
        print(f"Error fetching transactions for analytics: {e}")
        return {
            "best_seller_name": None,
            "stats": {
                "week": {"revenue": 0, "top_items": []},
                "month": {"revenue": 0, "top_items": []},
                "year": {"revenue": 0, "top_items": []}
            }
        }

    now = datetime.datetime.now()
    start_of_week = now - datetime.timedelta(days=now.weekday())
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    timeframes = {
        "week": {"start": start_of_week, "revenue": 0, "items": Counter()},
        "month": {"start": start_of_month, "revenue": 0, "items": Counter()},
        "year": {"start": start_of_year, "revenue": 0, "items": Counter()}
    }

    for txn in all_txns:
        try:
            created_at_str = txn.get('created_at', '').split('+')[0]
            txn_date = datetime.datetime.fromisoformat(created_at_str)
        except (ValueError, TypeError):
            continue

        total = float(txn.get('total_amount', 0))
        items = txn.get('items', [])
        if isinstance(items, str):
            try:
                items = json.loads(items)
            except:
                items = []

        for tf_name, tf_data in timeframes.items():
            if txn_date >= tf_data["start"]:
                tf_data["revenue"] += total
                for item in items:
                    name = item.get('name', 'Unknown')
                    qty = int(item.get('quantity', 0))
                    tf_data["items"][name] += qty

    # Format result
    result_stats = {}
    best_seller_name = None
    
    for tf_name, tf_data in timeframes.items():
        top_items = [
            {"name": name, "qty": qty} 
            for name, qty in tf_data["items"].most_common(5)
        ]
        result_stats[tf_name] = {
            "revenue": tf_data["revenue"],
            "top_items": top_items
        }
        if tf_name == "month" and top_items:
            best_seller_name = top_items[0]["name"]

    return {
        "best_seller_name": best_seller_name,
        "stats": result_stats
    }

@app.route('/')
def index():
    try:
        menu_response = supabase.table('menu').select("*").execute()
        raw_products = menu_response.data or []
        unavailable_ids = get_unavailable_ids()
        
        products = []
        for p in raw_products:
            p['is_available'] = p['id'] not in unavailable_ids
            products.append(p)

        analytics = calculate_analytics()
        best_seller_name = analytics["best_seller_name"]
    except Exception as e:
        print(f"Error in home route: {e}")
        products = []
        best_seller_name = None
        
    return render_template('index.html', products=products, best_seller_name=best_seller_name)

@app.route('/api/chart_data')
def get_chart_data():
    try:
        # Get last 7 days including today
        now = datetime.datetime.now()
        dates = [(now - datetime.timedelta(days=i)).date() for i in range(6, -1, -1)]
        labels = [d.strftime('%a') for d in dates] # Mon, Tue, etc.
        
        # Initialize revenue dict
        revenue_by_day = {d.isoformat(): 0 for d in dates}
        
        # Fetch transactions for the date range
        start_date = dates[0].isoformat()
        response = supabase.table('transactions').select("*").gte('created_at', start_date).execute()
        txns = response.data or []
        
        for txn in txns:
            try:
                created_at_str = txn.get('created_at', '').split('T')[0]
                if created_at_str in revenue_by_day:
                    revenue_by_day[created_at_str] += float(txn.get('total_amount', 0))
            except:
                continue
                
        values = [revenue_by_day[d.isoformat()] for d in dates]
        
        return jsonify({
            "labels": labels,
            "values": values
        })
    except Exception as e:
        print(f"Error fetching chart data: {e}")
        return jsonify({"labels": [], "values": []}), 500

@app.route('/api/stats')
def get_stats():
    analytics = calculate_analytics()
    response_data = analytics["stats"]
    response_data["best_seller_name"] = analytics["best_seller_name"]
    return jsonify(response_data)

@app.route('/api/toggle_stock/<int:item_id>', methods=['POST'])
def toggle_stock(item_id):
    unavailable_ids = get_unavailable_ids()
    if item_id in unavailable_ids:
        unavailable_ids.remove(item_id)
    else:
        unavailable_ids.append(item_id)
    save_unavailable_ids(unavailable_ids)
    return jsonify({"success": True, "unavailable_ids": unavailable_ids})

@app.route('/api/export_csv')
def export_csv():
    try:
        response = supabase.table('transactions').select("*").order('created_at', desc=True).execute()
        txns = response.data or []
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Order ID', 'Date', 'Total', 'Items'])
        
        for txn in txns:
            items_raw = txn.get('items', [])
            if isinstance(items_raw, str):
                try:
                    items_raw = json.loads(items_raw)
                except:
                    items_raw = []
            
            items_summary = ", ".join([f"{i.get('name')} x{i.get('quantity')}" for i in items_raw])
            writer.writerow([
                txn.get('order_id'),
                txn.get('created_at'),
                txn.get('total_amount'),
                items_summary
            ])
            
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=laporan_penjualan.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    except Exception as e:
        return str(e), 500

@app.route('/api/transactions', methods=['GET', 'POST'])
def handle_transactions():
    if request.method == 'POST':
        try:
            data = request.json
            order_id = "#ORD-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            items = data.get('items', [])
            total_amount = data.get('total', 0)
            
            transaction_data = {
                "order_id": order_id,
                "total_amount": total_amount,
                "items": items
            }
            
            response = supabase.table('transactions').insert(transaction_data).execute()
            if not response.data:
                raise Exception("Failed to insert transaction into Supabase")
                
            new_txn = response.data[0]
            analytics = calculate_analytics()
            
            return jsonify({
                "success": True,
                "order_id": order_id,
                "best_seller_name": analytics["best_seller_name"],
                "subtotal": data.get('subtotal', 0),
                "tax": data.get('tax', 0),
                "total": total_amount,
                "transaction": new_txn
            }), 201
        except Exception as e:
            print(f"Error saving transaction: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
            
    try:
        response = supabase.table('transactions').select("*").order('created_at', desc=True).execute()
        history = []
        for txn in response.data:
            txn['id'] = txn['order_id']
            txn['date'] = txn.get('created_at', datetime.datetime.now().isoformat())
            txn['total'] = txn['total_amount']
            history.append(txn)
        return jsonify(history)
    except Exception as e:
        print(f"Error fetching history: {e}")
        return jsonify([]), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
