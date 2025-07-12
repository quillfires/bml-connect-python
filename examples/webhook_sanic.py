from sanic import Sanic, response
from bml_connect import BMLConnect

app = Sanic("BMLWebhook")
client = BMLConnect(api_key="your_api_key", app_id="your_app_id")

@app.post('/webhook')
async def webhook(request):
    try:
        payload = request.json
        signature = payload.get('signature')
        
        if not signature:
            return response.json({"error": "Missing signature"}, status=400)
        
        if client.verify_webhook_signature(payload, signature):
            # Process webhook
            print(f"Received valid webhook: {payload}")
            return response.json({"status": "success"})
        else:
            return response.json({"error": "Invalid signature"}, status=403)
            
    except Exception as e:
        return response.json({"error": str(e)}, status=400)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)