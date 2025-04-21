# controllers/routes.py (o el archivo donde configuras tus endpoints)

from flask import Flask, request, jsonify, Blueprint
from controllers.bancoCentralController import get_exchange_rates
from dotenv import load_dotenv
# routes/paypalRoutes.py
from flask import Blueprint
from controllers.paypalController import create_payment

load_dotenv()

api_bp = Blueprint('api', __name__)

@api_bp.route('/exchange-rate', methods=['GET'])
def exchange_rate():
    # Recibir parámetros opcionales
    fecha_inicio = request.args.get('fecha_inicio', '13/11/2024')
    fecha_final = request.args.get('fecha_final', '13/11/2024')
    
    
    rates, error = get_exchange_rates(fecha_inicio, fecha_final)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"tipoDeCambio": rates})

# Crear un blueprint para las rutas de PayPal
paypal_routes = Blueprint('paypal_routes', __name__)

# Registrar la ruta para crear el pago con PayPal
@paypal_routes.route('/paypal/create-payment', methods=['POST'])
def paypal_create_payment():
    return create_payment()
