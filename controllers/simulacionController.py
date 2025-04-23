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

def formatear_fecha_vencimiento(fecha):
    """Convierte cualquier formato de fecha a MM/YY"""
    try:
        # Si ya está en formato MM/YY, devolverlo tal cual
        if isinstance(fecha, str) and re.match(r'^\d{2}/\d{2}$', fecha):
            return fecha
            
        # Si es una fecha completa, convertirla a MM/YY
        if isinstance(fecha, datetime.datetime):
            return fecha.strftime('%m/%y')
            
        # Si es una cadena con formato completo, intentar convertirla
        if isinstance(fecha, str):
            # Intentar varios formatos
            if "GMT" in fecha:
                # Formato: "Mon, 01 Nov 2027 00:00:00 GMT"
                try:
                    fecha_dt = datetime.datetime.strptime(fecha, "%a, %d %b %Y %H:%M:%S GMT")
                    return fecha_dt.strftime('%m/%y')
                except ValueError:
                    pass
                    
            # Intentar extraer mes y año con regex
            match = re.search(r'(\d{1,2})[/-](\d{2,4})', fecha)
            if match:
                mes = match.group(1).zfill(2)  # Asegurar 2 dígitos
                año = match.group(2)
                # Si el año tiene 4 dígitos, tomar solo los últimos 2
                if len(año) == 4:
                    año = año[2:]
                return f"{mes}/{año}"
                
            # Intentar con formato MM/YYYY
            match = re.search(r'(\d{1,2})/(\d{4})', fecha)
            if match:
                mes = match.group(1).zfill(2)
                año = match.group(2)[2:]  # Tomar solo los últimos 2 dígitos
                return f"{mes}/{año}"
    except Exception as e:
        print(f"Error al formatear fecha: {e}")
    
    # Si no se pudo formatear, devolver un formato por defecto
    return fecha

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
            # Formatear la fecha para que sea MM/YY
            fecha_vencimiento = formatear_fecha_vencimiento(row[1])
            
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

    # Formatear la fecha a MM/YY
    fecha_vencimiento = formatear_fecha_vencimiento(fecha_vencimiento)
    print(f"Fecha procesada: {fecha_vencimiento}")

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cursor = conn.cursor()
        
        # Consulta para buscar la tarjeta con la fecha formateada
        cursor.execute("""
            SELECT saldo, estado FROM tarjeta 
            WHERE numero_tarjeta = %s AND 
                  (fecha_vencimiento = %s OR 
                   FORMAT(fecha_vencimiento, 'MM/yy') = %s)
        """, (numero, fecha_vencimiento, fecha_vencimiento))

        row = cursor.fetchone()
        if not row:
            # Si no se encuentra, intentar con una consulta más flexible
            print("Tarjeta no encontrada con fecha exacta, intentando búsqueda flexible...")
            
            # Extraer mes y año de la fecha
            match = re.match(r'(\d{2})/(\d{2})', fecha_vencimiento)
            if match:
                mes = match.group(1)
                año = match.group(2)
                
                # Buscar tarjetas donde el mes y año coincidan
                cursor.execute("""
                    SELECT saldo, estado FROM tarjeta 
                    WHERE numero_tarjeta = %s AND 
                          MONTH(fecha_vencimiento) = %s AND 
                          (YEAR(fecha_vencimiento) %% 100) = %s
                """, (numero, int(mes), int(año)))
                
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
