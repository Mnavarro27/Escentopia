# controllers/paypalController.py

import os
import base64
import requests
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

paypal_bp = Blueprint('paypal', __name__)
CORS(paypal_bp)

PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_SECRET = os.environ.get('PAYPAL_SECRET')


# Debug temporal para verificar si las credenciales se están leyendo
print("CLIENT_ID:", PAYPAL_CLIENT_ID)
print("SECRET:", PAYPAL_SECRET[:4] + "****")  # Solo muestra los primeros 4 caracteres


def obtener_token():
    if not PAYPAL_CLIENT_ID or not PAYPAL_SECRET:
        raise Exception("Las credenciales de PayPal no están configuradas en las variables de entorno")
    auth_str = f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}"
    auth = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "client_credentials"
    }
    
    response = requests.post("https://api-m.sandbox.paypal.com/v1/oauth2/token", data=data, headers=headers, timeout=10)
    response.raise_for_status()
    token_info = response.json()
    return token_info.get("access_token")

@paypal_bp.route('/create-payment', methods=["POST", "OPTIONS"])
def create_payment():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.json
    total_amount = data.get("monto")
    
    if total_amount is None:
        return jsonify({"error": "El campo 'monto' es obligatorio."}), 400

    try:
        access_token = obtener_token()
    except Exception as e:
        print("Error obteniendo token:", e)
        return jsonify({"error": str(e)}), 500

    payment_data = {
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "transactions": [{
            "amount": {
                "total": f"{float(total_amount):.2f}",
                "currency": "USD"
            },
            "description": "Compra en Escentopia"
        }],
        "redirect_urls": {
            "return_url": "http://localhost:5000/finCompra",
            "cancel_url": "http://localhost:5000/finCompra"
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post("https://api-m.sandbox.paypal.com/v1/payments/payment", json=payment_data, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        error_info = e.response.json() if e.response else str(e)
        print("Error en la creación del pago:", error_info)
        return jsonify({"error": error_info}), 500

    response_data = response.json()
    approval_url = None
    for link in response_data.get("links", []):
        if link.get("rel") == "approval_url":
            approval_url = link.get("href")
            break

    if not approval_url:
        return jsonify({"error": "No se encontró la URL de aprobación en la respuesta de PayPal."}), 500

    return jsonify({"redirectUrl": approval_url})
