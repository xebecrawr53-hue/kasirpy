from flask import Flask, render_template, jsonify, request
import datetime
import random
import string
import os
import json
from collections import Counter
from supabase import create_client, Client

app = Flask(__name__)

# Supabase Configuration
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")
supabase: Client = create_client(url, key)

def calculate_analytics():
    try:
        response = supabase.table('transactions').select("*").execute()
        all_txns = response.data or []
    except Exception as e:
        print(f"Error fetching transactions for analytics: {e}")
        return {
            "best_seller_month": None,
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
        # Parse created_at. Example format: 2024-01-15T10:00:00.000000+00:00
        try:
            # Handle potential variations in ISO format
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
    best_seller_month = None
    
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
            best_seller_month = top_items[0]["name"]

    return {
        "best_seller_month": best_seller_month,
        "stats": result_stats
    }

@app.route('/')
def index():
    try:
        # Fetch menu
        menu_response = supabase.table('menu').select("*").execute()
        products = menu_response.data or []
        
        # Get analytics for Best Seller badge
        analytics = calculate_analytics()
        best_seller_name = analytics["best_seller_month"]
    except Exception as e:
        print(f"Error in home route: {e}")
        products = []
        best_seller_name = None
        
    return render_template('index.html', products=products, best_seller_name=best_seller_name)

@app.route('/api/stats')
def get_stats():
    analytics = calculate_analytics()
    return jsonify(analytics["stats"])

@app.route('/api/transactions', methods=['GET', 'POST'])
def handle_transactions():
    if request.method == 'POST':
        try:
            data = request.json
            order_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            items = data.get('items', [])
            total_amount = data.get('total', 0)
            
            transaction_data = {
                "order_id": order_id,
                "total_amount": total_amount,
                "items": items,
                "subtotal": data.get('subtotal', 0),
                "tax": data.get('tax', 0)
            }
            
            response = supabase.table('transactions').insert(transaction_data).execute()
            new_txn = response.data[0]
            new_txn['id'] = new_txn['order_id']
            new_txn['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return jsonify(new_txn), 201
        except Exception as e:
            print(f"Error saving transaction: {e}")
            return jsonify({"error": str(e)}), 500
            
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
