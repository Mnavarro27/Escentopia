# controllers/autenticacionController.py
from flask import Blueprint, request, jsonify
from flask_cors import CORS
import random
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

autenticacion_bp = Blueprint('autenticacion', __name__)
CORS(autenticacion_bp)

# Almacenamiento temporal de códigos 2FA (en producción usaría Redis o similar)
codigos_2fa = {}

def get_db_connection():
    # Importar la función desde app.py para evitar importación circular
    from app import get_db_connection as app_get_db
    return app_get_db()

def enviar_correo(destinatario, asunto, contenido):
    """Envía un correo electrónico usando SMTP"""
    try:
        # Configuración del servidor SMTP
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASS')
        
        # Crear mensaje
        msg = EmailMessage()
        msg.set_content(contenido)
        msg['Subject'] = asunto
        msg['From'] = smtp_user
        msg['To'] = destinatario
        
        # Enviar correo
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False

@autenticacion_bp.route('/solicitar-2fa', methods=['POST'])
def solicitar_2fa():
    """Genera y envía un código 2FA al correo del usuario"""
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({"error": "Nombre de usuario requerido"}), 400
    
    try:
        # Obtener correo del usuario
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT correo FROM Usuarios WHERE username = %s", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        correo = row[0]
        
        # Generar código 2FA (6 dígitos)
        codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Almacenar código (en producción usaría Redis con TTL)
        codigos_2fa[username] = codigo
        
        # Enviar correo con código
        asunto = "Código de verificación Escentopia"
        contenido = f"""
        Hola {username},
        
        Tu código de verificación para Escentopia es: {codigo}
        
        Este código expirará en 10 minutos.
        
        Saludos,
        Equipo Escentopia
        """
        
        if enviar_correo(correo, asunto, contenido):
            return jsonify({"success": True, "message": "Código enviado correctamente"}), 200
        else:
            return jsonify({"error": "Error al enviar el correo"}), 500
    
    except Exception as e:
        print(f"Error en solicitar-2fa: {e}")
        return jsonify({"error": str(e)}), 500

@autenticacion_bp.route('/verificar-2fa', methods=['POST'])
def verificar_2fa():
    """Verifica el código 2FA ingresado por el usuario"""
    data = request.json
    username = data.get('username')
    codigo = data.get('codigo2FA')
    
    if not username or not codigo:
        return jsonify({"error": "Datos incompletos"}), 400
    
    # Verificar código
    codigo_almacenado = codigos_2fa.get(username)
    if not codigo_almacenado:
        return jsonify({"error": "No hay código pendiente o ha expirado"}), 400
    
    if codigo != codigo_almacenado:
        return jsonify({"error": "Código incorrecto"}), 401
    
    # Eliminar código usado
    del codigos_2fa[username]
    
    return jsonify({"success": True, "message": "Verificación exitosa"}), 200
