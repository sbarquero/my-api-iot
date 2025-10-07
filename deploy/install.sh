#!/bin/bash
set -e

APP_NAME="mi-api-iot"
APP_USER="apiuser"
PROJECT_DIR="/opt/$APP_NAME"
VENV_DIR="$PROJECT_DIR/venv"

echo "🚀 Iniciando despliegue de $APP_NAME..."

# 1. Crear usuario
if ! id "$APP_USER" &>/dev/null; then
    sudo adduser --system --group --shell /bin/bash "$APP_USER"
fi

# 2. Instalar dependencias
sudo apt update
sudo apt install -y python3 python3-pip python3-venv apache2 mariadb-server

# 3. Configurar MariaDB
sudo mysql <<EOF
CREATE DATABASE IF NOT EXISTS sensor_db;
CREATE USER IF NOT EXISTS '$APP_USER'@'localhost' IDENTIFIED BY 'contraseña_segura_123';
GRANT ALL PRIVILEGES ON sensor_db.* TO '$APP_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

# 4. Copiar código
sudo mkdir -p "$PROJECT_DIR"
sudo cp -r app "$PROJECT_DIR/"
sudo cp requirements.txt "$PROJECT_DIR/"

# 5. Entorno virtual
sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

# 6. .env
sudo -u "$APP_USER" cp "$PROJECT_DIR/app/.env.example" "$PROJECT_DIR/app/.env"
sudo -u "$APP_USER" sed -i "s/your_secure_password_here/contraseña_segura_123/" "$PROJECT_DIR/app/.env"

# 7. Systemd
sudo cp deploy/systemd/mi-api-iot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mi-api-iot
sudo systemctl start mi-api-iot

# 8. Apache2
sudo a2enmod proxy proxy_http
sudo cp deploy/apache2/mi-api-iot.conf /etc/apache2/sites-available/
sudo a2ensite mi-api-iot
sudo apache2ctl configtest && sudo systemctl reload apache2

echo "✅ ¡Despliegue completado! Accede en: http://air12lite"
