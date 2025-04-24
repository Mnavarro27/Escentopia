# controllers/autenticacionController.py
from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
import random
import smtplib
import pytds
import ssl
from email.message import EmailMessage
import os
import sys
import traceback
from dotenv import load_dotenv

load_dotenv()

autenticacion_bp = Blueprint('autenticacion', __name__)
CORS(autenticacion_bp)

# Almacenamiento temporal de códigos 2FA (en producción usaría Redis o similar)
codigos_2fa = {}

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

def enviar_correo(destinatario, asunto, contenido, contenido_html=None):
    """Envía un correo electrónico usando SMTP"""
    try:
        # Configuración del servidor SMTP
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('EMAIL_USER')  # Usar EMAIL_USER en lugar de SMTP_USER
        smtp_pass = os.getenv('EMAIL_PASS')  # Usar EMAIL_PASS en lugar de SMTP_PASS
        
        # Verificar que tenemos las credenciales
        if not smtp_user or not smtp_pass:
            print("Error: Faltan credenciales SMTP en variables de entorno")
            return False
        
        # Crear mensaje
        msg = EmailMessage()
        msg.set_content(contenido)
        
        # Si hay contenido HTML, añadirlo como alternativa
        if contenido_html:
            msg.add_alternative(contenido_html, subtype='html')
            
        msg['Subject'] = asunto
        msg['From'] = smtp_user
        msg['To'] = destinatario
        
        # Enviar correo
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        traceback.print_exc()
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
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
                
            cursor = conn.cursor()
            cursor.execute("SELECT correo, nombre FROM Usuarios WHERE username = %s", (username,))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            correo, nombre = row
        finally:
            if conn:
                conn.close()
        
        # Generar código 2FA (6 dígitos)
        codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Almacenar código (en producción usaría Redis con TTL)
        codigos_2fa[username] = codigo
        
        # Contenido de texto plano
        contenido_texto = f"""
        Hola {nombre or username},
        
        Tu código de verificación para Escentopia es: {codigo}
        
        Este código expirará en 10 minutos.
        
        Saludos,
        Equipo Escentopia
        """
        
        # Contenido HTML mejorado
        contenido_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1a237e; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }}
                .code {{ font-size: 32px; font-weight: bold; color: #1a237e; letter-spacing: 5px; text-align: center; margin: 20px 0; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #777; text-align: center; }}
                .note {{ background-color: #e8eaf6; padding: 10px; border-left: 4px solid #3949ab; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Verificación de Seguridad</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre or username}</strong>,</p>
                    <p>Recibimos una solicitud para iniciar sesión en tu cuenta de Escentopia. Utiliza el siguiente código para completar el proceso:</p>
                    <div class="code">{codigo}</div>
                    <p>Este código expirará en 10 minutos por razones de seguridad.</p>
                    <div class="note">
                        <p><strong>Nota de seguridad:</strong> Si no intentaste iniciar sesión, alguien podría estar intentando acceder a tu cuenta. Te recomendamos ignorar este mensaje y verificar la seguridad de tu cuenta.</p>
                    </div>
                </div>
                <div class="footer">
                    <p>© 2025 Escentopia. Todos los derechos reservados.</p>
                    <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Enviar correo con ambos formatos
        if enviar_correo(correo, "Código de verificación Escentopia", contenido_texto, contenido_html):
            return jsonify({"success": True, "message": "Código enviado correctamente"}), 200
        else:
            return jsonify({"error": "Error al enviar el correo"}), 500
    
    except Exception as e:
        print(f"Error en solicitar-2fa: {e}")
        traceback.print_exc()
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

@autenticacion_bp.route('/registro', methods=['POST'])
def registro():
    """Registra un nuevo usuario en el sistema"""
    data = request.json
    nombre = data.get('nombre')
    username = data.get('username')
    password = data.get('password')
    correo = data.get('correo')
    
    if not nombre or not username or not password or not correo:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400
    
    # Validar formato de correo
    import re
    if not re.match(r"[^@]+@[^@]+\.[^@]+", correo):
        return jsonify({"error": "Formato de correo electrónico inválido"}), 400
    
    # Validar contraseña
    if len(password) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400
    
    if not re.search(r"[A-Z]", password):
        return jsonify({"error": "La contraseña debe tener al menos una letra mayúscula"}), 400
    
    if not re.search(r"[a-z]", password):
        return jsonify({"error": "La contraseña debe tener al menos una letra minúscula"}), 400
    
    if not re.search(r"\d", password):
        return jsonify({"error": "La contraseña debe tener al menos un número"}), 400
    
    if not re.search(r"[@$!%*?&+\-.:;,¿]", password):
        return jsonify({"error": "La contraseña debe tener al menos un carácter especial"}), 400
    
    try:
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
                
            cursor = conn.cursor()
            
            # Verificar si el usuario ya existe
            cursor.execute("SELECT id FROM Usuarios WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({"error": "El nombre de usuario ya está en uso"}), 400
            
            # Hashear la contraseña
            import bcrypt
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            # Insertar el nuevo usuario con valores predeterminados para columnas no proporcionadas
            cursor.execute(
                """
                INSERT INTO Usuarios (nombre, apellido, username, password, correo, telefono, tipo_identificacion, nuevo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (nombre, '', username, hashed_password, correo, '', 'Nacional', 1)
            )
            conn.commit()
            
            return jsonify({"success": True, "message": "Usuario registrado correctamente"}), 201
        finally:
            if conn:
                conn.close()
    except Exception as e:
        print(f"Error en registro: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500