#!/usr/bin/env bash
set -e

# ─── Render build script para instalar ODBC Driver 17 con dependencias ─────────
# Ejecutado con privilegios root en Render. No usar sudo.

# 1) Prerrequisitos: curl, apt-transport-https, gnupg
apt-get update
apt-get install -y curl apt-transport-https gnupg2 ca-certificates

# 2) Añadir el repositorio Microsoft y su clave
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# 3) Actualizar e instalar ODBC driver y desarrollo
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# 4) Mostrar librerías instaladas para diagnóstico
echo "Verificando instalación de msodbcsql17:"
ls -l /opt/microsoft/msodbcsql17/lib64 || true

# 5) Instalar dependencias Python
echo "Instalando dependencias Python..."
pip install -r requirements.txt
