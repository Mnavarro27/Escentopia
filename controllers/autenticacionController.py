from flask import Blueprint, request, jsonify
import os
import random
import datetime
import ssl
import smtplib
from email.message import EmailMessage
from flask import current_app as app

autenticacion_bp = Blueprint('autenticacion', __name__)

@autenticacion_bp.route('/solicitar-2fa', methods=['POST'])
def solicitar_2fa():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username requerido"}), 400

    try:
        # Buscar correo del usuario
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT correo, nombre FROM Usuarios WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Usuario no encontrado"}), 404

        correo, nombre = row

        # Generar código 2FA
        codigo = str(random.randint(100000, 999999))
        expiracion = datetime.datetime.now() + datetime.timedelta(minutes=10)

        # Guardarlo en la memoria temporal de Flask
        if '2FA' not in app.config:
            app.config['2FA'] = {}
        app.config['2FA'][username] = (codigo, expiracion)

        # Crear correo con formato HTML mejorado
        msg = EmailMessage()
        
        # Contenido HTML mejorado
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }}
                .code {{ font-size: 32px; font-weight: bold; color: #4CAF50; letter-spacing: 5px; text-align: center; margin: 20px 0; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #777; text-align: center; }}
                .note {{ background-color: #fff8e1; padding: 10px; border-left: 4px solid #ffc107; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Verificación de Seguridad</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre if nombre else username}</strong>,</p>
                    <p>Para completar tu inicio de sesión en Escentopia, utiliza el siguiente código de verificación:</p>
                    <div class="code">{codigo}</div>
                    <p>Este código expirará en 10 minutos por razones de seguridad.</p>
                    <div class="note">
                        <p><strong>Nota de seguridad:</strong> Si no has intentado iniciar sesión en Escentopia, alguien podría estar intentando acceder a tu cuenta. Te recomendamos cambiar tu contraseña inmediatamente.</p>
                    </div>
                </div>
                <div class="footer">
                    <p>© 2023 Escentopia. Todos los derechos reservados.</p>
                    <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Configurar el correo
        msg.set_content(f"Tu código de verificación para Escentopia es: {codigo}\nEste código expirará en 10 minutos.")
        msg.add_alternative(html_content, subtype='html')
        msg['Subject'] = "Código de verificación - Escentopia"
        msg['From'] = os.getenv("EMAIL_USER")
        msg['To'] = correo

        # Enviar el correo
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            server.send_message(msg)

        return jsonify({"message": "Código enviado"}), 200

    except Exception as e:
        print("Error solicitando 2FA:", e)
        return jsonify({"error": "No se pudo enviar el código 2FA"}), 500

@autenticacion_bp.route('/verificar-2fa', methods=['POST'])
def verificar_2fa():
    data = request.json
    username = data.get('username')
    codigo = data.get('codigo2FA')
    
    if not username or not codigo:
        return jsonify({"error": "Faltan datos requeridos"}), 400
    
    # Verificar si hay una entrada 2FA para este usuario
    entry = app.config.get('2FA', {}).get(username)
    if not entry:
        return jsonify({"error": "No se ha solicitado verificación para este usuario"}), 400
    
    stored_code, exp = entry
    
    # Verificar si el código ha expirado
    if datetime.datetime.now() > exp:
        del app.config['2FA'][username]
        return jsonify({"error": "El código ha expirado. Por favor, solicita uno nuevo."}), 400
    
    # Verificar si el código es correcto
    if codigo != stored_code:
        return jsonify({"error": "Código incorrecto"}), 401
    
    # Si todo está bien, eliminar la entrada y devolver éxito
    del app.config['2FA'][username]
    return jsonify({"success": True, "message": "Código verificado correctamente"})


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
            
            # Verificar si el correo ya existe
            cursor.execute("SELECT id FROM Usuarios WHERE correo = %s", (correo,))
            if cursor.fetchone():
                return jsonify({"error": "El correo electrónico ya está registrado"}), 400
            
            # Hashear la contraseña
            import bcrypt
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            # Insertar el nuevo usuario
            cursor.execute(
                """
                INSERT INTO Usuarios (nombre, username, password, correo, nuevo)
                VALUES (%s, %s, %s, %s, 1)
                """,
                (nombre, username, hashed_password, correo)
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
