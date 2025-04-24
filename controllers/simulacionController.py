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
    """Convierte una fecha MM/YY al primer día del mes siguiente en formato YYYY-MM-DD para SQL Server"""
    try:
        if isinstance(fecha, str) and re.match(r'^\d{2}/\d{2}$', fecha):
            mes, año = fecha.split('/')
            # Asumir que el año es 20XX (por ejemplo, 26 -> 2026)
            año_completo = f"20{año}"
            # Convertir a número para cálculos
            mes_num = int(mes)
            año_num = int(año_completo)
            # Sumar un mes para obtener el mes siguiente
            if mes_num == 12:
                mes_num = 1
                año_num += 1
            else:
                mes_num += 1
            # Crear una fecha con el primer día del mes siguiente
            fecha_dt = datetime.datetime.strptime(f"{mes_num}/01/{año_num}", "%m/%d/%Y")
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
        print(f"Fecha procesada: {fecha_dt}, Mes: {fecha_dt.month}, Año: {fecha_dt.year}")

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cursor = conn.cursor()
        
        # Depuración: Verificar si la tarjeta existe
        cursor.execute("SELECT numero_tarjeta, fecha_vencimiento FROM tarjeta WHERE numero_tarjeta = %s", (numero,))
        tarjeta = cursor.fetchone()
        if not tarjeta:
            print(f"No se encontró tarjeta con número: {numero}")
            return jsonify({"validacion": "rechazada", "motivo": "Tarjeta no encontrada"}), 404
        
        print(f"Tarjeta encontrada: Número: {tarjeta[0]}, Fecha en DB: {tarjeta[1]}")

        # Consulta para buscar la tarjeta comparando la fecha completa
        cursor.execute("""
            SELECT saldo, estado FROM tarjeta 
            WHERE numero_tarjeta = %s AND 
                  fecha_vencimiento = %s
        """, (numero, fecha_dt.date()))

        row = cursor.fetchone()
        if not row:
            print(f"No se encontró coincidencia para fecha: {fecha_dt.date()}")
            return jsonify({"validacion": "rechazada", "motivo": "Fecha de vencimiento no coincide"}), 404

        saldo, estado = row
        print(f"Saldo: {saldo}, Estado: {estado}")

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