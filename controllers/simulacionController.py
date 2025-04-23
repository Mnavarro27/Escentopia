# controllers/simulacionController.py
from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
from decimal import Decimal
import random, pyodbc
import smtplib
import pytds
import ssl
from email.message import EmailMessage
import os
import sys
import traceback
from dotenv import load_dotenv

simulacion_bp = Blueprint('simulacion', __name__)
CORS(simulacion_bp)

def get_db_connection():
    """Obtiene una conexión a la base de datos usando pytds"""
    try:
        server = os.getenv('DB_SERVER')
        port = int(os.getenv('DB_PORT', '1433'))
        database = os.getenv('DB_NAME')
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASS')
        cafile = '/etc/ssl/certs/ca-certificates.crt'

        return pytds.connect(
            server=server,
            port=port,
            database=database,
            user=user,
            password=password,
            timeout=30,
            tds_version=1946157060,
            cafile=cafile,
            validate_host=False
        )
    except Exception as e:
        print(f"Error de conexión a la base de datos: {e}")
        traceback.print_exc()
        return None

# controllers/simulacionController.py
@simulacion_bp.route("/validar-pago", methods=["POST"])
def validar_pago():
    data = request.json
    print("🔍 Datos recibidos:", data)

    numero = data.get("numero")
    fecha_vencimiento = data.get("fecha_vencimiento")
    monto = data.get("monto")

    if not numero or not fecha_vencimiento or not monto:
        return jsonify({"error": "Faltan datos"}), 400

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cursor = conn.cursor()

        cursor.execute("""
            SELECT saldo, estado FROM tarjeta 
            WHERE numero_tarjeta = %s AND fecha_vencimiento = %s
        """, (numero, fecha_vencimiento))

        row = cursor.fetchone()
        if not row:
            return jsonify({"validacion": "rechazada", "motivo": "Tarjeta no encontrada"}), 404

        saldo, estado = row
        if estado != "activa":
            return jsonify({"validacion": "rechazada", "motivo": "Tarjeta inactiva"}), 403

        if saldo < float(monto):
            return jsonify({"validacion": "rechazada", "motivo": "Fondos insuficientes"}), 402

        # Descontar el saldo simulado
        nuevo_saldo = saldo - Decimal(str(monto))

        cursor.execute("UPDATE tarjeta SET saldo = %s WHERE numero_tarjeta = %s", (nuevo_saldo, numero))
        conn.commit()

        return jsonify({"validacion": "aprobada", "nuevo_saldo": float(nuevo_saldo)}), 200

    except Exception as e:
        print("❌ ERROR BACKEND:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
  
@simulacion_bp.route("/tarjetas", methods=["GET"])
def obtener_tarjetas():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cursor = conn.cursor()
        cursor.execute("SELECT numero_tarjeta, fecha_vencimiento, propietario FROM tarjeta WHERE estado = 'activa'")
        tarjetas = []
        for row in cursor.fetchall():
            tarjetas.append({
                "numero_tarjeta": row[0],
                "fecha_vencimiento": row[1],
                "propietario": row[2]
            })
        return jsonify(tarjetas)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
