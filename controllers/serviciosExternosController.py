from flask import Blueprint, request, jsonify
import pyodbc
from flask_cors import CORS

servicios_bp = Blueprint('servicios_externos', __name__)
CORS(servicios_bp)

def get_db():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=simulacionesApi;"
        "UID=sa;"
        "PWD=AdminM27"
    )

# 🔹 Servicio 1: Ministerio de Salud
@servicios_bp.route('/salud/componente/<nombre>', methods=["GET"])
def validar_componente(nombre):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT permitido FROM componentes_salud WHERE nombre = ?", nombre)
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Componente no encontrado"}), 404
    return jsonify({"permitido": bool(row[0])})

@servicios_bp.route('/salud/componentes', methods=["POST"])
def agregar_componente():
    data = request.json
    nombre = data.get("nombre")
    permitido = data.get("permitido")

    if not nombre or permitido is None:
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO componentes_salud (nombre, permitido) VALUES (?, ?)", nombre, int(permitido))
        conn.commit()
        conn.close()
        return jsonify({"mensaje": "Componente agregado correctamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🔹 Servicio 2: Transporte
@servicios_bp.route('/transporte/disponibilidad', methods=["GET"])
def verificar_transporte():
    provincia = request.args.get("provincia")
    canton = request.args.get("canton")
    distrito = request.args.get("distrito")

    if not provincia or not canton or not distrito:
        return jsonify({"error": "Faltan parámetros"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT disponible FROM transporte_envios
        WHERE provincia = ? AND canton = ? AND distrito = ?
    """, provincia, canton, distrito)
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"disponible": False, "mensaje": "Zona no registrada"}), 200
    return jsonify({"disponible": bool(row[0])})

@servicios_bp.route('/transporte', methods=["POST"])
def agregar_transporte():
    data = request.json
    provincia = data.get("provincia")
    canton = data.get("canton")
    distrito = data.get("distrito")
    disponible = data.get("disponible")

    if not provincia or not canton or not distrito or disponible is None:
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO transporte_envios (provincia, canton, distrito, disponible) VALUES (?, ?, ?, ?)", provincia, canton, distrito, int(disponible))
        conn.commit()
        conn.close()
        return jsonify({"mensaje": "Zona registrada correctamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🔹 Servicio 3: RecipientesCR
@servicios_bp.route('/recipientes/<tipo>', methods=["GET"])
def consultar_recipientes(tipo):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT cantidad FROM recipientes WHERE tipo = ?", tipo)
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Tipo de recipiente no encontrado"}), 404
    return jsonify({"cantidad": row[0]})

@servicios_bp.route('/recipientes', methods=["POST"])
def agregar_recipiente():
    data = request.json
    tipo = data.get("tipo")
    cantidad = data.get("cantidad")

    if not tipo or cantidad is None:
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO recipientes (tipo, cantidad) VALUES (?, ?)", tipo, cantidad)
        conn.commit()
        conn.close()
        return jsonify({"mensaje": "Recipiente agregado correctamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
