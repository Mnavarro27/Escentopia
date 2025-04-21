from flask import Blueprint, request, jsonify
import os
import random
import datetime
import ssl
import smtplib
import bcrypt
from email.message import EmailMessage
from flask import current_app as app

recuperacion_bp = Blueprint('recuperacion', __name__)

@recuperacion_bp.route('/enviar-token', methods=['POST'])
def enviar_token():
    data = request.json
    username = data.get('username')
    email = data.get('email')

    if not username or not email:
        return jsonify({"error": "Nombre de usuario y correo electrónico son requeridos"}), 400

    try:
        # Buscar usuario en la base de datos
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM Usuarios WHERE username = ? AND correo = ?", (username, email))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "No se encontró un usuario con ese nombre de usuario y correo electrónico"}), 404

        user_id, nombre = row

        # Generar token de recuperación
        token = str(random.randint(100000, 999999))
        expiracion = datetime.datetime.now() + datetime.timedelta(minutes=10)

        # Guardarlo en la memoria temporal de Flask
        if 'RECOVERY_TOKENS' not in app.config:
            app.config['RECOVERY_TOKENS'] = {}
        app.config['RECOVERY_TOKENS'][username] = (token, expiracion)

        # Enviar correo con el token
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
                    <h1>Recuperación de Contraseña</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre if nombre else username}</strong>,</p>
                    <p>Recibimos una solicitud para restablecer tu contraseña en Escentopia. Utiliza el siguiente código para continuar con el proceso:</p>
                    <div class="code">{token}</div>
                    <p>Este código expirará en 10 minutos por razones de seguridad.</p>
                    <div class="note">
                        <p><strong>Nota de seguridad:</strong> Si no solicitaste restablecer tu contraseña, alguien podría estar intentando acceder a tu cuenta. Te recomendamos ignorar este mensaje y verificar la seguridad de tu cuenta.</p>
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
        msg.set_content(f"Tu código de recuperación para Escentopia es: {token}\nEste código expirará en 10 minutos.")
        msg.add_alternative(html_content, subtype='html')
        msg['Subject'] = "Recuperación de contraseña - Escentopia"
        msg['From'] = os.getenv("EMAIL_USER")
        msg['To'] = email

        # Enviar el correo
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            server.send_message(msg)

        return jsonify({"message": "Código enviado al correo electrónico"}), 200

    except Exception as e:
        print("Error enviando token:", e)
        return jsonify({"error": "No se pudo enviar el código de recuperación"}), 500

@recuperacion_bp.route('/verificar-token', methods=['POST'])
def verificar_token():
    data = request.json
    username = data.get('username')
    codigo = data.get('codigo')
    
    if not username or not codigo:
        return jsonify({"error": "Faltan datos requeridos"}), 400
    
    # Verificar si hay un token para este usuario
    entry = app.config.get('RECOVERY_TOKENS', {}).get(username)
    if not entry:
        return jsonify({"error": "No se ha solicitado recuperación para este usuario"}), 400
    
    stored_token, exp = entry
    
    # Verificar si el token ha expirado
    if datetime.datetime.now() > exp:
        del app.config['RECOVERY_TOKENS'][username]
        return jsonify({"error": "El código ha expirado. Por favor, solicita uno nuevo."}), 400
    
    # Verificar si el token es correcto
    if codigo != stored_token:
        return jsonify({"error": "Código incorrecto"}), 401
    
    # Si todo está bien, eliminar la entrada y devolver éxito
    del app.config['RECOVERY_TOKENS'][username]
    return jsonify({"success": True, "message": "Código verificado correctamente"})

@recuperacion_bp.route('/verificar-pregunta', methods=['POST'])
def verificar_pregunta():
    data = request.json
    username = data.get('username')
    pregunta = data.get('pregunta')
    respuesta = data.get('respuesta')
    
    
    if not username or not pregunta or not respuesta:
        return jsonify({"error": "Faltan datos requeridos"}), 400
    
    try:
        # Buscar usuario y verificar pregunta de seguridad
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si la tabla tiene las columnas de pregunta y respuesta
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'Usuarios' AND COLUMN_NAME = 'preguntaSeguridad'
        """)
        
        pregunta_exists = cursor.fetchone()[0] > 0
        
        if not pregunta_exists:
            # Si no existe, intentar crearla
            try:
                cursor.execute(
                    "ALTER TABLE Usuarios ADD preguntaSeguridad NVARCHAR(255)"
                )
                cursor.execute(
                    "ALTER TABLE Usuarios ADD respuestaSeguridad NVARCHAR(255)"
                )
                conn.commit()
            except Exception as e:
                print("Error al crear columnas de seguridad:", e)
                return jsonify({"error": "No se pudo verificar la pregunta de seguridad"}), 500
        
        # Consultar la pregunta y respuesta del usuario
        cursor.execute(
            "SELECT preguntaSeguridad, respuestaSeguridad FROM Usuarios WHERE username = ?", (username,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if not row or not row[0] or not row[1]:
            return jsonify({"error": "No se encontró información de seguridad para este usuario"}), 404
        
        stored_pregunta, stored_respuesta = row
        
        # Verificar que la pregunta coincida
        if pregunta != stored_pregunta:
            return jsonify({"error": "La pregunta de seguridad no coincide"}), 401
        
        # Verificar que la respuesta coincida (sin distinguir mayúsculas/minúsculas)
        if respuesta.lower() != stored_respuesta.lower():
            return jsonify({"error": "Respuesta incorrecta"}), 401
        
        # Si todo está bien, devolver éxito
        return jsonify({"success": True, "message": "Verificación exitosa"})
        
    except Exception as e:
        print("Error verificando pregunta:", e)
        return jsonify({"error": "No se pudo verificar la pregunta de seguridad"}), 500

@recuperacion_bp.route('/cambiar-contrasena', methods=['POST'])
def cambiar_contrasena():
    data = request.json
    identificador = data.get('identificador')  # Puede ser username o email
    nueva_password = data.get('nuevaPassword')
    
    if not identificador or not nueva_password:
        return jsonify({"error": "Faltan datos requeridos"}), 400
    
    try:
        # Buscar usuario por username o email
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Intentar primero por username
        cursor.execute("SELECT id FROM Usuarios WHERE username = ?", (identificador,))
        row = cursor.fetchone()
        
        # Si no se encuentra, intentar por email
        if not row:
            cursor.execute("SELECT id FROM Usuarios WHERE correo = ?", (identificador,))
            row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({"error": "No se encontró el usuario"}), 404
        
        user_id = row[0]
        
        # Hashear la nueva contraseña
        hashed_password = bcrypt.hashpw(nueva_password.encode(), bcrypt.gensalt()).decode()
        
        # Actualizar la contraseña
        cursor.execute(
            "UPDATE Usuarios SET password = ?, intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id = ?",
            (hashed_password, user_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Contraseña actualizada correctamente"})
        
    except Exception as e:
        print("Error cambiando contraseña:", e)
        return jsonify({"error": "No se pudo actualizar la contraseña"}), 500
