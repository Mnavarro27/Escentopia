
# ─── Render build script para instalar ODBC Driver 17 ─────────────────────────
# Este script se ejecuta con privilegios de root en Render, no necesita sudo.

# 1) Añadir el repositorio de Microsoft
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list \
     > /etc/apt/sources.list.d/mssql-release.list

# 2) Actualizar e instalar driver y dependencias
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev unixodbc-dev

# 3) Instalar dependencias Python
echo "Instalando dependencias Python..."
pip install -r requirements.txt
