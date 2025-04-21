# Usa una imagen base con Python
FROM python:3.11-slim

# Variables de entorno (opcional)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Instalar paquetes de sistema y driver ODBC
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     curl apt-transport-https gnupg2 unixodbc-dev \
  && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
  && curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list \
     > /etc/apt/sources.list.d/mssql-release.list \
  && ACCEPT_EULA=Y apt-get update \
  && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
  && rm -rf /var/lib/apt/lists/*

# Copiar tu código y dependencias
COPY requirements.txt .

# Instalar las dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la app
COPY . .

# Exponer el puerto que usa Render
EXPOSE 10000

# Comando de arranque
CMD ["python", "app.py"]
