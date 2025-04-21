# controllers/registroCivilController.py
import pyodbc
from flask import Blueprint, request, jsonify
from flask_cors import CORS

registro_bp = Blueprint('registro', __name__)
CORS(registro_bp)

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=simulacionesApi;"
        "UID=sa;"
        "PWD=AdminM27"
    )
    

@registro_bp.route("/consultar-usuario/<cedula>", methods=["GET"])
def consultar_usuario(cedula):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE cedula = ?", (cedula,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"mensaje": "Usuario no encontrado"}), 404

        columnas = [col[0] for col in cursor.description]
        datos = dict(zip(columnas, row))
        return jsonify(datos), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
