from flask import Flask, render_template, jsonify, request
import datetime
import random
import string
import os
import json
from supabase import create_client, Client

app = Flask(__name__)

# Supabase Configuration
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")
supabase: Client = create_client(url, key)

@app.route('/')
def index():
    try:
        # 1. Menu Fetching: home route pulls data from the 'menu' table
        response = supabase.table('menu').select("*").execute()
        products = response.data
    except Exception as e:
        print(f"Error fetching menu: {e}")
        products = []
        
    return render_template('index.html', products=products)

@app.route('/api/transactions', methods=['GET', 'POST'])
def handle_transactions():
    if request.method == 'POST':
        try:
            data = request.json
            
            # Generate a realistic transaction record
            order_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            items = data.get('items', [])
            total_amount = data.get('total', 0)
            
            # 2. Saving Orders: INSERT the successful order into the 'transactions' table in Supabase
            # Items column is JSONB, so we pass the list directly (postgrest handles it)
            transaction_data = {
                "order_id": order_id,
                "total_amount": total_amount,
                "items": items,
                "subtotal": data.get('subtotal', 0),
                "tax": data.get('tax', 0)
            }
            
            response = supabase.table('transactions').insert(transaction_data).execute()
            
            # Add formatted date for the receipt UI (since Supabase might return it in a different format)
            new_txn = response.data[0]
            new_txn['id'] = new_txn['order_id'] # Map for frontend compatibility
            new_txn['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return jsonify(new_txn), 201
        except Exception as e:
            print(f"Error saving transaction: {e}")
            return jsonify({"error": str(e)}), 500
            
    # 3. History Page: fetch data from the 'transactions' table in Supabase
    try:
        response = supabase.table('transactions').select("*").order('created_at', desc=True).execute()
        # Map fields for frontend compatibility
        history = []
        for txn in response.data:
            txn['id'] = txn['order_id']
            # Supabase timestamps are ISO, let's keep them or format them if needed
            # The frontend expects 'date'
            txn['date'] = txn.get('created_at', datetime.datetime.now().isoformat())
            txn['total'] = txn['total_amount']
            history.append(txn)
        return jsonify(history)
    except Exception as e:
        print(f"Error fetching history: {e}")
        return jsonify([]), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
