import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Variables de configuración
DB_NAME = os.getenv('DB_NAME', 'sensor_db')
DB_USER = os.getenv('DB_USER', 'apiuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
API_KEY = os.getenv('API_KEY', 'mi-api-key-segura-por-defecto')
SHOW_DB_ERRORS = os.getenv("SHOW_DB_ERRORS", "false").lower() == "true"
