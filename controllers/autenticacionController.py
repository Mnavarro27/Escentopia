from flask import Blueprint, request, jsonify
import os
import random
import datetime
import ssl
import smtplib
import bcrypt
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
    # Importar aquí para romper ciclo de imports
    from app import get_db_connection

    data = request.get_json() or {}

    # 1) Campos obligatorios
    for field in ('username', 'nombre', 'correo', 'password'):
        if not data.get(field):
            return jsonify({"error": f"Falta campo obligatorio: {field}"}), 400

    # 2) Hashear contraseña
    hashed = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
    

    # 3) Valores por defecto para columnas NOT NULL
    apellido            = data.get('apellido')            or ""
    tipo_identificacion = data.get('tipoIdentificacion') or ""
    identificacion      = data.get('identificacion')      or ""
    fecha_nacimiento    = data.get('fechaNacimiento')     or "1900-01-01"
    sexo                = data.get('sexo')                or ""
    direccion           = data.get('direccion')           or ""
    telefono            = data.get('telefono')            or ""
    preguntaSec         = data.get('preguntaSeguridad')   or ""
    respuestaSec        = data.get('respuestaSeguridad')  or ""
    nombre_tarjeta      = data.get('nombreTarjeta')       or ""
    numero_tarjeta      = data.get('numeroTarjeta')       or ""
    fecha_vencimiento   = data.get('fechaVencimiento')    or ""
    codigo_seguridad    = data.get('codigoSeguridad')     or ""
    pais_id             = data.get('pais')                or ""
    provincia_id        = data.get('provincia')           or ""
    canton_id           = data.get('canton')              or ""
    distrito_id         = data.get('distrito')            or ""

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Usuarios (
              username, nombre, correo, password,
              apellido, tipo_identificacion, identificacion,
              fecha_nacimiento, sexo, direccion, telefono,
              preguntaSeguridad, respuestaSeguridad,
              nombre_tarjeta, numero_tarjeta, fecha_vencimiento,
              codigo_seguridad, pais_id, provincia_id, canton_id, distrito_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        data['username'], data['nombre'], data['correo'], hashed,
        apellido, tipo_identificacion, identificacion,
        fecha_nacimiento, sexo, direccion, telefono,
        preguntaSec, respuestaSec,
        nombre_tarjeta, numero_tarjeta, fecha_vencimiento,
        codigo_seguridad, pais_id, provincia_id, canton_id, distrito_id
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Registrado"}), 201

    except Exception as e:
        app.logger.error(f"Error en registro: {e}")
        return jsonify({"error": str(e)}), 500