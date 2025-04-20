# controllers/api.py
from flask import Blueprint, jsonify
from datetime import datetime
from controllers.bancoCentralController import get_exchange_rates

api = Blueprint('api', __name__)

@api.route('/exchange-rate')
def exchange_rate():
    # pide el tipo de cambio para hoy
    today = datetime.today().strftime('%Y-%m-%d')
    tipo_cambio, error = get_exchange_rates(today, today)

    if error or not tipo_cambio:
        # devuelve siempre la misma estructura
        return jsonify({
            "tipoDeCambio": {
                "compra": "0.00",
                "venta": "0.00"
            },
            "error": error
        }), 500

    return jsonify({
        "tipoDeCambio": {
            "compra": tipo_cambio.get("compra", "0.00"),
            "venta":  tipo_cambio.get("venta",  "0.00")
        }
    }), 200
