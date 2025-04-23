# controllers/simulacionController.py
from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
from decimal import Decimal
import random
import smtplib
import pytds
import ssl
from email.message import EmailMessage
import os
import sys
import traceback
from dotenv import load_dotenv
import datetime

load_dotenv()

# Crear el blueprint sin tilde en el nombre
simulacion_bp = Blueprint('simulacion', __name__, url_prefix='/api/simulacion')
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

@simulacion_bp.route("/tarjetas", methods=["GET"])
def obtener_tarjetas():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cursor = conn.cursor()
        # Modificar la consulta para usar BIT en lugar de 'activa'
        cursor.execute("SELECT numero_tarjeta, fecha_vencimiento, propietario FROM tarjeta WHERE estado = 1")
        tarjetas = []
        for row in cursor.fetchall():
            # Formatear la fecha para que sea más simple
            fecha_vencimiento = row[1]
            if isinstance(fecha_vencimiento, datetime.datetime):
                fecha_vencimiento = fecha_vencimiento.strftime('%m/%Y')
            
            tarjetas.append({
                "numero_tarjeta": row[0],
                "fecha_vencimiento": fecha_vencimiento,
                "propietario": row[2]
            })
        return jsonify(tarjetas)
    except Exception as e:
        print(f"Error al obtener tarjetas: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@simulacion_bp.route("/validar-pago", methods=["POST"])
def validar_pago():
    data = request.json
    print("🔍 Datos recibidos:", data)

    numero = data.get("numero")
    fecha_vencimiento = data.get("fecha_vencimiento")
    monto = data.get("monto")

    if not numero or not fecha_vencimiento or not monto:
        return jsonify({"error": "Faltan datos"}), 400

    # Procesar la fecha de vencimiento si viene en formato GMT
    try:
        if isinstance(fecha_vencimiento, str) and "GMT" in fecha_vencimiento:
            # Intentar parsear la fecha completa
            try:
                # Formato: "Mon, 01 Nov 2027 00:00:00 GMT"
                fecha_dt = datetime.datetime.strptime(fecha_vencimiento, "%a, %d %b %Y %H:%M:%S GMT")
                fecha_vencimiento = fecha_dt.strftime('%m/%Y')
            except ValueError:
                # Si falla, intentar extraer mes y año con un enfoque más simple
                import re
                match = re.search(r'\d{2} (\w{3}) (\d{4})', fecha_vencimiento)
                if match:
                    mes = match.group(1)
                    año = match.group(2)
                    # Convertir mes de texto a número
                    meses = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06", 
                             "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
                    fecha_vencimiento = f"{meses.get(mes, '01')}/{año}"
    except Exception as e:
        print(f"Error al procesar fecha: {e}")
        # Si hay error, mantener la fecha original

    print(f"Fecha procesada: {fecha_vencimiento}")

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cursor = conn.cursor()
        
        # Consulta más flexible para la fecha de vencimiento
        cursor.execute("""
            SELECT saldo, estado FROM tarjeta 
            WHERE numero_tarjeta = %s AND 
                  (fecha_vencimiento = %s OR 
                   CONVERT(VARCHAR(7), fecha_vencimiento, 101) = %s OR
                   CONVERT(VARCHAR(7), fecha_vencimiento, 110) = %s)
        """, (numero, fecha_vencimiento, fecha_vencimiento, fecha_vencimiento))

        row = cursor.fetchone()
        if not row:
            return jsonify({"validacion": "rechazada", "motivo": "Tarjeta no encontrada"}), 404

        saldo, estado = row
        # Verificar el estado como BIT (1 = activa, 0 = inactiva)
        if estado != 1:
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
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
