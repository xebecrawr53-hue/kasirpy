from flask import Flask, render_template, jsonify, request
import datetime
import random
import string
import os
import json
from supabase import create_client, Client
import random
from datetime import datetime

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
    # --- SKENARIO 1: MENYIMPAN TRANSAKSI (Saat Klik Pay) ---
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # 1. Buat ID Order Random
            new_order_id = f"#ORD-{random.randint(1000, 9999)}"
            
            # 2. Ambil data dari Frontend
            # Kita pakai .get() biar gak error kalau datanya kosong
            items_data = data.get('items', [])
            if not items_data:
                items_data = data.get('cart', []) # Jaga-jaga kalau namanya 'cart'
            
            total_price = data.get('total', 0)
            if total_price == 0:
                total_price = data.get('total_amount', 0)

            # 3. Siapkan Bungkusan Data untuk Supabase
            transaction_payload = {
                "order_id": new_order_id,
                "total_amount": total_price,
                "items": items_data  # Ini akan otomatis jadi JSONB di Supabase
            }

            # 4. KIRIM KE SUPABASE
            supabase.table('transactions').insert(transaction_payload).execute()

            # 5. Beri respon sukses ke Frontend
            return jsonify({
                "success": True, 
                "message": "Saved to Supabase", 
                "order_id": new_order_id
            })

        except Exception as e:
            print(f"GAGAL SIMPAN TRANSAKSI: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    # --- SKENARIO 2: MENGAMBIL HISTORY (Saat Buka Tab History) ---
    else:
        try:
            # Ambil semua data dari tabel transactions, urutkan dari yang terbaru
            response = supabase.table('transactions').select("*").order('created_at', desc=True).execute()
            return jsonify(response.data)
        except Exception as e:
            print(f"GAGAL AMBIL HISTORY: {e}")
            return jsonify([])
            
            # 2. Saving Orders: INSERT the successful order into the 'transactions' table in Supabase
            # Items column is JSONB, so we pass the list directly (postgrest handles it)
        
            
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
