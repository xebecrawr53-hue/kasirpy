from flask import Flask, render_template, jsonify, request
import datetime
import random
import string
import os
from supabase import create_client, Client

app = Flask(__name__)

# Supabase Configuration
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")
supabase: Client = create_client(url, key)

# In-memory transaction history
transactions = []

@app.route('/')
def index():
    try:
        # Fetch all items from the 'menu' table in Supabase
        response = supabase.table('menu').select("*").execute()
        products = response.data
    except Exception as e:
        print(f"Error fetching menu: {e}")
        products = []
        
    return render_template('index.html', products=products)

@app.route('/api/transactions', methods=['GET', 'POST'])
def handle_transactions():
    if request.method == 'POST':
        data = request.json
        
        # Generate a realistic transaction record
        transaction = {
            "id": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": data.get('items', []),
            "subtotal": data.get('subtotal', 0),
            "tax": data.get('tax', 0),
            "total": data.get('total', 0)
        }
        transactions.insert(0, transaction) # Add to beginning
        return jsonify(transaction), 201
        
    return jsonify(transactions)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
