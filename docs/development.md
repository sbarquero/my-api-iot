# 🧪 Guía de Desarrollo en WSL2

Esta guía explica cómo configurar y probar la API en **Windows 11 + WSL2** antes de desplegar en producción.

---

## 📋 Requisitos

- Windows 11 Pro
- WSL2 con Ubuntu 22.04/24.04
- Python 3.8+
- MariaDB

---

## 🚀 Configuración inicial

### 1. Instalar dependencias del sistema
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install apache2 mariadb-server python3 python3-pip python3-venv git -y
```

### 2. Configurar MariaDB
```bash
sudo mysql_secure_installation
# Sigue los pasos y anota la contraseña de root
```

### 3. Crear base de datos y usuario
```bash
sudo mysql -u root -p
```
```sql
CREATE DATABASE sensor_db;
CREATE USER 'apiuser'@'localhost' IDENTIFIED BY 'contraseña_de_desarrollo';
GRANT ALL PRIVILEGES ON sensor_db.* TO 'apiuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 📁 Estructura del proyecto

Clona o crea tu proyecto en WSL2:

```bash
mkdir -p ~/my-api-iot
cd ~/my-api-iot
```

Estructura esperada:
```
my-api-iot/
├── app/
│   ├── main.py
│   └── ...
├── venv/               # Se creará automáticamente
├── requirements.txt
└── .env
```

---

## ⚙️ Configuración del entorno

### 1. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
```bash
cp .env.example .env
nano .env
```
Ejemplo para desarrollo:
```env
DB_NAME=sensor_db
DB_USER=apiuser
DB_PASSWORD=contraseña_de_desarrollo
SHOW_DB_ERRORS=true
```

---

## ▶️ Ejecutar la API

### Modo desarrollo (con recarga automática)
```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Acceder desde Windows
- API: http://localhost:8000
- Documentación: http://localhost:8000/docs

---

## 🔄 Scripts de utilidad

### Iniciar servidor completo
```bash
# Crea ~/start-server.sh con este contenido:
#!/bin/bash
cd ~/my-api-iot
source venv/bin/activate
sudo systemctl start mariadb
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```bash
chmod +x ~/start-server.sh
./start-server.sh
```

### Detener servidor
```bash
# Crea ~/stop-server.sh:
#!/bin/bash
pkill -f "uvicorn app.main:app"
sudo systemctl stop mariadb  # Opcional
```

---

## 🧪 Pruebas con ESP32

Desde tu ESP32, envía datos a:
```
http://nombre_servidor.local:8000/data
```

> 💡 Asegúrate de que:
> - El nombre `nombre_servidor` esté configurado en Windows
> - El firewall de Windows permita el puerto 8000
> - MariaDB esté en ejecución

---

## 📤 Preparar para producción

Antes de subir a GitHub:

1. **Actualiza dependencias**:
   ```bash
   pip freeze > requirements.txt
   ```

2. **Verifica que `.env` no esté en Git**:
   ```bash
   echo ".env" >> .gitignore
   git add .gitignore
   ```

3. **Sube los cambios**:
   ```bash
   git add .
   git commit -m "Actualización para producción"
   git push origin main
   ```

---

## 🛠️ Solución de problemas comunes

### Error: "Access denied for user 'root'@'localhost'"
- Usa `sudo mysql` para acceder sin contraseña
- O crea un usuario dedicado como se muestra arriba

### MariaDB no inicia
```bash
sudo systemctl start mariadb
sudo systemctl status mariadb
```

### Puerto 8000 bloqueado
- Verifica que no haya otra instancia de Uvicorn corriendo
- Usa `lsof -i :8000` para identificar el proceso

---

### Verificar estructura final:
```bash
tree -L 2
```
Deberías ver:
```
.
├── LICENSE
├── README.md
├── app/
├── docs/
│   └── development.md
├── requirements.txt
└── ...
```
