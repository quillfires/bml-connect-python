from flask import Flask, request, jsonify
from bml_connect import BMLConnect

app = Flask(__name__)
client = BMLConnect(api_key="your_api_key", app_id="your_app_id")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        payload = request.get_json()
        signature = payload.get('signature')
        
        if not signature:
            return jsonify({"error": "Missing signature"}), 400
        
        if client.verify_webhook_signature(payload, signature):
            # Process verified webhook
            transaction_id = payload['transactionId']
            status = payload['status']
            amount = payload['amount']
            
            print(f"Received webhook for transaction {transaction_id}")
            print(f"Status: {status}, Amount: {amount}")
            
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"error": "Invalid signature"}), 403
            
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)