#!/bin/bash
set -e

APP_NAME="my-api-iot"
APP_USER="apiuser"
PROJECT_DIR="/opt/$APP_NAME"
VENV_DIR="$PROJECT_DIR/venv"

echo "🚀 Iniciando despliegue de $APP_NAME..."

# 1. Crear usuario
if ! id "$APP_USER" &>/dev/null; then
    echo "Creando usuario del sistema: $APP_USER"
    sudo adduser --system --group --shell /bin/bash "$APP_USER"
else
    echo "El usuario '$APP_USER' ya existe. Continuando..."
fi

# 2. Instalar dependencias
echo "Instalando dependencias del sistema..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv apache2 mariadb-server

# 3. Configurar MariaDB
echo "Configurando base de datos MariaDB..."
sudo mysql <<EOF
CREATE DATABASE IF NOT EXISTS sensor_db;
CREATE USER IF NOT EXISTS '$APP_USER'@'localhost' IDENTIFIED BY 'contraseña_segura_123';
GRANT ALL PRIVILEGES ON sensor_db.* TO '$APP_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

# 4. Copiar código
echo "Creando directorio del proyecto en $PROJECT_DIR..."
sudo mkdir -p "$PROJECT_DIR"
echo "Copiando archivos del proyecto a $PROJECT_DIR..."
sudo cp -r app "$PROJECT_DIR/"
echo "Copiando requirements.txt a $PROJECT_DIR..."
sudo cp requirements.txt "$PROJECT_DIR/"

# 5. Entorno virtual
echo "Creando entorno virtual en $VENV_DIR..."
#sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"
sudo python3 -m venv "$VENV_DIR"

echo "Instalando dependencias de Python..."
# sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
sudo "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

# 6. .env
echo "Configurando archivo .env..."
#sudo -u "$APP_USER" cp "$PROJECT_DIR/app/.env.example" "$PROJECT_DIR/app/.env"
sudo cp "$PROJECT_DIR/app/.env.example" "$PROJECT_DIR/app/.env"

echo "Actualizando configuración de la base de datos en .env..."
# sudo -u "$APP_USER" sed -i "s/your_secure_password_here/contraseña_segura_123/" "$PROJECT_DIR/app/.env"
sudo sed -i "s/your_secure_password_here/contraseña_segura_123/" "$PROJECT_DIR/app/.env"

# 7. Systemd
echo "Configurando servicio systemd..."
sudo cp deploy/systemd/my-api-iot.service /etc/systemd/system/
echo "Recargando daemon de systemd..."
sudo systemctl daemon-reload
echo "Habilitando y arrancando el servicio $APP_NAME..."
sudo systemctl enable my-api-iot
echo "Iniciando el servicio $APP_NAME..."
sudo systemctl start my-api-iot

# 8. Apache2
echo "Configurando Apache2 como proxy inverso..."
sudo a2enmod proxy proxy_http
echo "Copiando configuración de Apache2..."
sudo cp deploy/apache2/my-api-iot.conf /etc/apache2/sites-available/
echo "Habilitando sitio en Apache2..."
sudo a2ensite my-api-iot
echo "Probando configuración de Apache2..."
sudo apache2ctl configtest && sudo systemctl reload apache2

echo "✅ ¡Despliegue completado! Accede en: http://air12lite"
