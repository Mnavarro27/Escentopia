# controllers/simulacionController.py
import pyodbc
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from decimal import Decimal

simulacion_bp = Blueprint('simulacion', __name__)
CORS(simulacion_bp)

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=simulacionesApi;"
        "UID=sa;"
        "PWD=AdminM27"
    )

# controllers/simulacionController.py
@simulacion_bp.route("/validar-pago", methods=["POST"])
def validar_pago():
    data = request.json
    print("🔍 Datos recibidos:", data)  # <-- AGREGAR ESTO

    numero = data.get("numero")
    fecha_vencimiento = data.get("fecha_vencimiento")
    monto = data.get("monto")

    if not numero or not fecha_vencimiento or not monto:
        return jsonify({"error": "Faltan datos"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT saldo, estado FROM tarjeta 
            WHERE numero_tarjeta = ? AND fecha_vencimiento = ?
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

        cursor.execute("UPDATE tarjeta SET saldo = ? WHERE numero_tarjeta = ?", (nuevo_saldo, numero))
        conn.commit()

        return jsonify({"validacion": "aprobada", "nuevo_saldo": nuevo_saldo}), 200

    except Exception as e:
        print("❌ ERROR BACKEND:", e)  # <-- AGREGAR ESTO TAMBIÉN
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
  
@simulacion_bp.route("/tarjetas", methods=["GET"])
def obtener_tarjetas():
    try:
        conn = get_connection()
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
        conn.close()
        
