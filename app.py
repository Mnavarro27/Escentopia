import os,json,base64,random,datetime,bcrypt,requests,ssl,smtplib,pyodbc,pytds

from flask import (
  Flask, request, jsonify,
  send_from_directory, render_template,
  make_response
)
from flask_cors import CORS
from email.message import EmailMessage
from dotenv import load_dotenv

# Importar blueprints
from controllers.api import api
from controllers.simulacionController import simulacion_bp
from controllers.paypalController import paypal_bp
from controllers.recuperacionController import recuperacion_bp
from controllers.autenticacionController import autenticacion_bp

# ─── Carga .env ────────────────────────────────────────────────────────────────
load_dotenv()

# ─── Configuración de Flask ────────────────────────────────────────────────────
app = Flask(
  __name__,
  static_folder="views/static",
  static_url_path="/static",
  template_folder="views/templates"
)
CORS(app)

# Registrar blueprints
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(simulacion_bp, url_prefix='/api/simulacion')
app.register_blueprint(paypal_bp, url_prefix='/api/paypal')
app.register_blueprint(recuperacion_bp, url_prefix='/api/recuperacion')
app.register_blueprint(autenticacion_bp, url_prefix='/api/autenticacion')

# ─── Páginas estáticas (HTML) ──────────────────────────────────────────────────
@app.route('/')
@app.route('/<page>.html')
def serve_page(page='index'):
  html = render_template(f'{page}.html')
  response = make_response(html)
  response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
  response.headers['Pragma'] = 'no-cache'
  response.headers['Expires'] = '0'
  return response

# ─── PWA: manifest.json & Service Worker ───────────────────────────────────────
@app.route('/manifest.json')
def manifest():
  return send_from_directory(app.static_folder, 'manifest.json')

@app.route('/sw.js')
def service_worker():
  return send_from_directory(app.static_folder, 'sw.js')

# ─── Imágenes fuera de /static/images ──────────────────────────────────────────
@app.route('/images/<path:filename>')
def serve_image(filename):
  return send_from_directory('images', filename)

# ─── Configuración de la base de datos ─────────────────────────────────────────
# Las variables de entorno deben configurarse en Render: DB_SERVER, DB_PORT, DB_NAME, DB_USER, DB_PASS

def get_db_connection():
    """
    Conecta a Azure SQL usando el driver python-tds para evitar dependencias ODBC.
    Variables de entorno requeridas:
    - DB_SERVER
    - DB_PORT (opcional, por defecto 1433)
    - DB_NAME
    - DB_USER
    - DB_PASS
    """
    server = os.getenv('DB_SERVER')
    port = int(os.getenv('DB_PORT', '1433'))
    database = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASS')

    # Conexión básica sin parámetros no soportados (host/encrypted) por python-tds
    return pytds.connect(
        server=server,
        port=port,
        database=database,
        user=user,
        password=password,
        timeout=30,
        tds_version=1946157060  # Equivale a TDS 7.4
    )

def buffer_to_base64(buffer):
  if buffer:
      return "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')
  return "/static/images/default.jpg"

# ─── Auditoría de accesos ───────────────────────────────────────────────────────
def log_audit(username, ip, success, reason):
  try:
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO Auditoria_Accesos (username, ip, exito, motivo) VALUES (?, ?, ?, ?)",
          username, ip, success, reason
      )
      conn.commit()
      conn.close()
  except Exception as e:
      print("Error auditando acceso:", e)
# ─── Endpoints de API ──────────────────────────────────────────────────────────

# Rutas para 2FA (para compatibilidad)
@app.route('/solicitar-2fa', methods=['POST'])
def solicitar_2fa_compat():
  from controllers.autenticacionController import solicitar_2fa
  return solicitar_2fa()

@app.route('/verificar-2fa', methods=['POST'])
def verificar_2fa_compat():
  from controllers.autenticacionController import verificar_2fa
  return verificar_2fa()

# Productos
@app.route('/productos', methods=['GET'])
def get_productos():
  try:
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute("SELECT id, nombre, precio, imagen FROM Productos")
      productos = [
          {"id": id, "nombre": nombre, "precio": float(precio), "imagen": imagen_url}
          for id, nombre, precio, imagen_url in cursor.fetchall()
      ]
      conn.close()
      
      # Crear respuesta con headers para evitar caché
      response = jsonify(productos)
      response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
      response.headers['Pragma'] = 'no-cache'
      response.headers['Expires'] = '0'
      
      return response
  except Exception as e:
      print("Error al obtener productos:", e)
      return jsonify({"error": str(e)}), 500

# Perfil: GET y PUT
@app.route('/perfil', methods=['GET', 'PUT'])
def perfil():
    if request.method == 'GET':
        username = request.args.get('username')
        if not username:
            return jsonify({"error": "Username requerido"}), 400
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar si existen las columnas de pregunta y respuesta
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Usuarios' AND COLUMN_NAME = 'preguntaSeguridad'
            """)
            
            pregunta_exists = cursor.fetchone()[0] > 0
            
            if not pregunta_exists:
                # Si no existen, intentar crearlas
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
            
            # Consulta principal
            cursor.execute("""
                SELECT U.*, P.nombre AS pais, PR.nombre AS provincia,
                       C.nombre AS canton, D.nombre AS distrito,
                       U.preguntaSeguridad, U.respuestaSeguridad
                FROM Usuarios U
                LEFT JOIN Paises P ON U.pais_id = P.id
                LEFT JOIN Provincias PR ON U.provincia_id = PR.id
                LEFT JOIN Cantones C ON U.canton_id = C.id
                LEFT JOIN Distritos D ON U.distrito_id = D.id
                WHERE U.username = ?
            """, username)
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({"error": "Usuario no encontrado"}), 404
                
            # Crear diccionario con los resultados
            columns = [column[0] for column in cursor.description]
            perfil = dict(zip(columns, row))
            
            conn.close()
            
            # Crear respuesta con headers para evitar caché
            response = jsonify(perfil)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            return response
        except Exception as e:
            print("Error perfil GET:", e)
            return jsonify({"error": "Error servidor"}), 500

    else:  # PUT
        data = request.json
        username = data.get('username')
        if not username:
            return jsonify({"error": "Username obligatorio"}), 400
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM Usuarios WHERE username = ?", username)
            if not cursor.fetchone():
                conn.close()
                return jsonify({"error": "Usuario no existe"}), 404
            
            # Verificar si existen las columnas de pregunta y respuesta
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Usuarios' AND COLUMN_NAME = 'preguntaSeguridad'
            """)
            
            pregunta_exists = cursor.fetchone()[0] > 0
            
            if not pregunta_exists:
                # Si no existen, intentar crearlas
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

            # Actualizar perfil incluyendo pregunta y respuesta de seguridad
            cursor.execute("""
                UPDATE Usuarios SET
                  nombre=?, apellido=?, telefono=?, correo=?, direccion=?,
                  tipo_identificacion=?, identificacion=?, fecha_nacimiento=?,
                  sexo=?, nombre_tarjeta=?, numero_tarjeta=?, fecha_vencimiento=?,
                  codigo_seguridad=?, pais_id=?, provincia_id=?, canton_id=?, distrito_id=?,
                  preguntaSeguridad=?, respuestaSeguridad=?
                WHERE username=?
            """,
            data.get('nombre'),
            data.get('apellido'),
            data.get('telefono'),
            data.get('correo'),
            data.get('direccion'),
            data.get('tipoIdentificacion'),
            data.get('identificacion'),
            data.get('fechaNacimiento'),
            data.get('sexo'),
            data.get('nombreTarjeta'),
            data.get('numeroTarjeta'),
            data.get('fechaVencimiento'),
            data.get('codigoSeguridad'),
            data.get('pais'),
            data.get('provincia'),
            data.get('canton'),
            data.get('distrito'),
            data.get('preguntaSeguridad'),
            data.get('respuestaSeguridad'),
            username)
            
            conn.commit()
            conn.close()
            return jsonify({"message": "Perfil actualizado"})
        except Exception as e:
            print("Error perfil PUT:", e)
            return jsonify({"error": "Error servidor"}), 500

# Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    ip = request.remote_addr
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, username, password, intentos_fallidos, bloqueado_hasta
            FROM Usuarios WHERE username=?
        """, username)
        row = cursor.fetchone()
        if not row:
            log_audit(username, ip, 0, "No encontrado")
            conn.close()
            return jsonify({"error": "Credenciales incorrectas"}), 401

        user_id, nombre, user_username, hashed, attempts, blocked_until = row
        now = datetime.datetime.now()
        if blocked_until and blocked_until > now:
            log_audit(username, ip, 0, "Bloqueado")
            conn.close()
            return jsonify({"error": "Cuenta bloqueada"}), 403

        if not bcrypt.checkpw(password.encode(), hashed.encode()):
            attempts = (attempts or 0) + 1
            if attempts >= 3:
                blocked_until = now + datetime.timedelta(minutes=5)
                cursor.execute(
                    "UPDATE Usuarios SET intentos_fallidos=?, bloqueado_hasta=? WHERE username=?",
                    attempts, blocked_until, username
                )
            else:
                cursor.execute(
                    "UPDATE Usuarios SET intentos_fallidos=? WHERE username=?",
                    attempts, username
                )
            conn.commit()
            log_audit(username, ip, 0, "Contraseña incorrecta")
            conn.close()
            return jsonify({"error": f"Credenciales incorrectas. Restan {3-attempts} intentos"}), 401

        # Éxito
        cursor.execute(
            "UPDATE Usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL WHERE username=?",
            username
        )
        conn.commit()
        log_audit(username, ip, 1, "Éxito")
        conn.close()
        return jsonify({"usuario": {"id": user_id, "nombre": nombre, "username": user_username}})
    except Exception as e:
        print("Error login:", e)
        return jsonify({"error": "Error servidor"}), 500

# Geografía
@app.route('/paises', methods=['GET'])
def get_paises():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id,nombre FROM Paises")
        paises = [{"id": r[0], "nombre": r[1]} for r in cursor.fetchall()]
        conn.close()
        
        # Crear respuesta con headers para evitar caché
        response = jsonify(paises)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    except Exception as e:
        print("Error paises:", e)
        return jsonify({"error":"Error servidor"}), 500

@app.route('/provincias', methods=['GET'])
def get_provincias():
    pais = request.args.get('pais')
    if not pais:
        return jsonify({"error":"País requerido"}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id,nombre FROM Provincias WHERE pais_id=?", pais)
        provs = [{"id":r[0],"nombre":r[1]} for r in cursor.fetchall()]
        conn.close()
        
        # Crear respuesta con headers para evitar caché
        response = jsonify(provs)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    except Exception as e:
        print("Error provincias:", e)
        return jsonify({"error":"Error servidor"}), 500

@app.route('/cantones', methods=['GET'])
def get_cantones():
    prov = request.args.get('provincia')
    if not prov:
        return jsonify({"error":"Provincia requerida"}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id,nombre FROM Cantones WHERE provincia_id=?", prov)
        cants = [{"id":r[0],"nombre":r[1]} for r in cursor.fetchall()]
        conn.close()
        
        # Crear respuesta con headers para evitar caché
        response = jsonify(cants)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    except Exception as e:
        print("Error cantones:", e)
        return jsonify({"error":"Error servidor"}), 500

@app.route('/distritos', methods=['GET'])
def get_distritos():
    cant = request.args.get('canton')
    if not cant:
        return jsonify({"error":"Cantón requerido"}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id,nombre FROM Distritos WHERE canton_id=?", cant)
        dist = [{"id":r[0],"nombre":r[1]} for r in cursor.fetchall()]
        conn.close()
        
        # Crear respuesta con headers para evitar caché
        response = jsonify(dist)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    except Exception as e:
        print("Error distritos:", e)
        return jsonify({"error":"Error servidor"}), 500

# Añadir esta ruta para actualizar el estado de onboarding
@app.route('/actualizar-onboarding', methods=['POST'])
def actualizar_onboarding():
    data = request.json
    username = data.get('username')
    onboarding_completed = data.get('onboardingCompleted', False)
    
    if not username:
        return jsonify({"error": "Username requerido"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si existe la columna 'nuevo' en la tabla Usuarios
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'Usuarios' AND COLUMN_NAME = 'nuevo'
        """)
        
        column_exists = cursor.fetchone()[0] > 0
        
        if column_exists:
            # Si la columna existe, actualizar el valor
            cursor.execute(
                "UPDATE Usuarios SET nuevo = ? WHERE username = ?",
                0 if onboarding_completed else 1, username
            )
        else:
            # Si la columna no existe, intentar crearla
            try:
                cursor.execute(
                    "ALTER TABLE Usuarios ADD nuevo BIT DEFAULT 1"
                )
                cursor.execute(
                    "UPDATE Usuarios SET nuevo = ? WHERE username = ?",
                    0 if onboarding_completed else 1, username
                )
            except Exception as e:
                print("Error al crear columna 'nuevo':", e)
                # No hacemos nada, seguimos usando localStorage
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Estado de onboarding actualizado"})
    
    except Exception as e:
        print("Error al actualizar estado de onboarding:", e)
        return jsonify({"error": "Error al actualizar estado de onboarding"}), 500
    
    import requests

@app.route('/_outbound-ip')
def outbound_ip():
    # Hacemos una petición a un servicio externo para que nos devuelva nuestra IP pública
    ip = requests.get('https://api.ipify.org').text
    return jsonify({"outbound_ip": ip})

@app.route("/_db-test")
def db_test():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({"status": "ok", "msg": "Conexión a la DB exitosa"}), 200
    except Exception as e:
        # Devolvemos el texto del error para que aparezca en los logs y en la respuesta HTTP
        return jsonify({"status": "error", "error": str(e)}), 500



# ─── Arranque de la app ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
