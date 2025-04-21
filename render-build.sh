#!/usr/bin/env bash
set -e

# 1) Añadir el repositorio de Microsoft (requiere sudo)
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list \
     | sudo tee /etc/apt/sources.list.d/mssql-release.list

# 2) Actualizar e instalar driver y dependencias con sudo
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# 3) Instalar dependencias Python
pip install -r requirements.txt
