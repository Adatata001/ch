from flask import Flask, request, jsonify, render_template
import os
import requests
from dotenv import load_dotenv
from utils import generate_signature, get_timestamp

app = Flask(__name__)
load_dotenv()

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Railway environment variables
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
WALLET = os.getenv('WALLET_ADDRESS')

@app.route('/inject-money', methods=['POST'])
def handle_injection():
    amount = request.json.get('amount')

    endpoint = "https://api.bybit.com/v5/asset/deposit/history"
    timestamp = get_timestamp()

    payload = f"amount={amount}&address={WALLET}&timestamp={timestamp}"
    signature = generate_signature(API_SECRET, payload)

    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

    response = requests.post(endpoint, headers=headers, data=payload)

    return jsonify({
        "status": "Attempted",
        "response": response.json() if response.ok else response.text
    })

if __name__ == '__main__':
    app.run(debug=True)