#!/usr/bin/env bash
set -e

# 1) Agregar el repositorio de Microsoft
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list \
     > /etc/apt/sources.list.d/mssql-release.list

# 2) Actualizar e instalar driver y dependencias
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# 3) Instalar tus dependencias Python
pip install -r requirements.txt
