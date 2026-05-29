from flask import Flask, request, jsonify, render_template
import os
import requests
import uuid
from urllib.parse import urlencode
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
BYBIT_BASE_URL = os.getenv('BYBIT_BASE_URL', 'https://api.bybit.com').rstrip('/')
RECV_WINDOW = '5000'
TRAINING_DEPOSITS = []


def bybit_get(path, params=None):
    if not API_KEY or not API_SECRET:
        return {"error": "API_KEY and API_SECRET must be configured."}, 500

    params = {key: value for key, value in (params or {}).items() if value not in (None, '')}
    query_string = urlencode(params)
    timestamp = get_timestamp()
    signature_payload = f"{timestamp}{API_KEY}{RECV_WINDOW}{query_string}"
    signature = generate_signature(API_SECRET, signature_payload)

    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": RECV_WINDOW,
    }

    url = f"{BYBIT_BASE_URL}{path}"
    response = requests.get(url, headers=headers, params=params, timeout=15)
    try:
        body = response.json()
    except ValueError:
        body = {"error": response.text}

    return body, response.status_code

@app.route('/inject-money', methods=['POST'])
def handle_injection():
    return jsonify({
        "status": "Rejected",
        "message": (
            "Bybit's deposit API cannot create money or force a deposit. "
            "Send funds on-chain to your Bybit deposit address, then use /deposit-records "
            "to check whether Bybit has credited it."
        )
    }), 400


@app.route('/training/inject-deposit', methods=['POST'])
def training_inject_deposit():
    data = request.get_json(silent=True) or {}
    address = (data.get('address') or WALLET or '').strip()
    coin = (data.get('coin') or 'USDT').upper()
    chain = (data.get('chain') or 'ETH').upper()
    amount = str(data.get('amount') or '').strip()

    if not address:
        return jsonify({"error": "address is required"}), 400

    try:
        numeric_amount = float(amount)
    except ValueError:
        return jsonify({"error": "amount must be a number"}), 400

    if numeric_amount <= 0:
        return jsonify({"error": "amount must be greater than zero"}), 400

    record = {
        "trainingOnly": True,
        "status": "synthetic_deposit_created",
        "id": str(uuid.uuid4()),
        "txID": f"training-{uuid.uuid4().hex}",
        "coin": coin,
        "chain": chain,
        "amount": amount,
        "toAddress": address,
        "createdAt": get_timestamp(),
        "note": "Synthetic local event only. No blockchain transaction or exchange credit occurred.",
    }
    TRAINING_DEPOSITS.insert(0, record)

    return jsonify(record), 201


@app.route('/training/deposits')
def training_deposits():
    return jsonify({
        "trainingOnly": True,
        "rows": TRAINING_DEPOSITS,
    })


@app.route('/deposit-address')
def deposit_address():
    coin = request.args.get('coin', 'USDT').upper()
    chain_type = request.args.get('chainType') or request.args.get('chain')
    body, status_code = bybit_get('/v5/asset/deposit/query-address', {
        'coin': coin,
        'chainType': chain_type,
    })
    return jsonify(body), status_code


@app.route('/deposit-records')
def deposit_records():
    coin = request.args.get('coin', 'USDT').upper()
    limit = request.args.get('limit', '10')
    body, status_code = bybit_get('/v5/asset/deposit/query-record', {
        'coin': coin,
        'limit': limit,
    })
    return jsonify(body), status_code

if __name__ == '__main__':
    app.run(debug=True)
