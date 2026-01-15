from flask import Flask, render_template, jsonify, request
import datetime
import random
import string

app = Flask(__name__)

# --- Data ---
# Pre-filled 8 luxury Warkop items
PRODUCTS = [
    {
        "id": 1,
        "name": "Nasi Goreng",
        "price": 85000,
        "image": "https://images.unsplash.com/photo-1512058560366-cd242d5f1f96?auto=format&fit=crop&q=80&w=1000",
        "category": "Food"
    },
    {
        "id": 2,
        "name": "Indomie Truffle",
        "price": 45000,
        "image": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?auto=format&fit=crop&q=80&w=1000",
        "category": "Food"
    },
    {
        "id": 3,
        "name": "Kopi Gula Aren Premium",
        "price": 35000,
        "image": "https://images.unsplash.com/photo-1541167760496-1628856ab772?auto=format&fit=crop&q=80&w=1000",
        "category": "Beverage"
    },
    {
        "id": 4,
        "name": "Roti Bakar Belgian Choco",
        "price": 42000,
        "image": "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&q=80&w=1000", # Toast image
        "category": "Food"
    },
    {
        "id": 5,
        "name": "Pisang Goreng Keju",
        "price": 28000,
        "image": "https://images.unsplash.com/photo-1627308595229-7830a5c91f9f?auto=format&fit=crop&q=80&w=1000", # Fried snack
        "category": "Food"
    },
    {
        "id": 6,
        "name": "Matcha Latte",
        "price": 38000,
        "image": "https://images.unsplash.com/photo-1515823064-d6e0c04616a7?auto=format&fit=crop&q=80&w=1000",
        "category": "Beverage"
    },
    {
        "id": 7,
        "name": "Teh Tarik Aceh",
        "price": 25000,
        "image": "https://images.unsplash.com/photo-1597318181409-cf64d0b5d8a2?auto=format&fit=crop&q=80&w=1000", # Tea
        "category": "Beverage"
    },
    {
        "id": 8,
        "name": "Mineral Water (Equil)",
        "price": 20000,
        "image": "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?auto=format&fit=crop&q=80&w=1000",
        "category": "Beverage"
    }
]

# In-memory transaction history
transactions = []

@app.route('/')
def index():
    return render_template('index.html', products=PRODUCTS)

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
