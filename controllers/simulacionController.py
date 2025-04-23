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
import re

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

def parse_fecha_vencimiento(fecha):
    """Convierte una fecha MM/YY a un objeto datetime para SQL Server"""
    try:
        if isinstance(fecha, str) and re.match(r'^\d{2}/\d{2}$', fecha):
            mes, año = fecha.split('/')
            # Asumir que el año es 20XX (por ejemplo, 26 -> 2026)
            año_completo = f"20{año}"
            # Crear una fecha con el primer día del mes
            fecha_dt = datetime.datetime.strptime(f"{mes}/01/{año_completo}", "%m/%d/%Y")
            return fecha_dt
        else:
            raise ValueError(f"Formato de fecha inválido: {fecha}")
    except Exception as e:
        print(f"Error al parsear fecha: {e}")
        raise

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
            # Convertir la fecha de la base de datos (2026-12-01) a MM/YY
            fecha_vencimiento = row[1].strftime('%m/%y') if isinstance(row[1], datetime.datetime) else row[1]
            
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

    try:
        # Convertir la fecha MM/YY a un objeto datetime
        fecha_dt = parse_fecha_vencimiento(fecha_vencimiento)
        print(f"Fecha procesada: {fecha_dt}")

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cursor = conn.cursor()
        
        # Consulta para buscar la tarjeta comparando mes y año
        cursor.execute("""
            SELECT saldo, estado FROM tarjeta 
            WHERE numero_tarjeta = %s AND 
                  MONTH(fecha_vencimiento) = %s AND 
                  YEAR(fecha_vencimiento) = %s
        """, (numero, fecha_dt.month, fecha_dt.year))

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