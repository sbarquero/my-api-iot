from fastapi import FastAPI, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional

# --- CONFIGURACIÓN INICIAL ---
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Leer variable de entorno para mostrar errores
SHOW_DB_ERRORS = os.getenv("SHOW_DB_ERRORS", "false").lower() == "true"

# Configurar esquema de autenticación
security = HTTPBearer()

# Obtener la API Key desde .env
API_KEY = os.getenv("API_KEY", "mi-api-key-segura-por-defecto")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")
    return credentials.credentials

app = FastAPI(title="API IoT", description="Recibe y sirve datos de sensores")

# --- MODELO DE DATOS ---
class SensorData(BaseModel):
    sensor_id: str
    value: float

# --- MODELO DE RESPUESTA ---
class SensorDataResponse(BaseModel):
    id: int
    sensor_id: str
    value: float
    timestamp: str  # Devolverá formato ISO 8601 con 'Z'

# --- FUNCIÓN DE CONEXIÓN A BASE DE DATOS ---
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database=os.getenv('DB_NAME', 'sensor_db'),
            user=os.getenv('DB_USER', 'apiuser'),
            password=os.getenv('DB_PASSWORD', '')
        )
        return connection
    except Error as e:
        error_msg = f"Error al conectar con la base de datos: {str(e)}"
        logger.error(error_msg)
        if SHOW_DB_ERRORS:
            raise HTTPException(status_code=500, detail=f"Error DB: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Error interno del servidor")

# --- FUNCIONES DE AYUDA ---
def format_timestamp_to_iso_z(timestamp_str: str) -> str:
    """
    Convierte un timestamp de MariaDB (ej: '2025-10-10 14:02:21') a formato ISO 8601 con 'Z'
    """
    try:
        # Convertir string a datetime
        dt = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
        # Formatear como ISO 8601 con 'Z' (UTC)
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        # Si no se puede parsear, devolver tal cual
        return timestamp_str

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"mensaje": "¡Servidor FastAPI + MariaDB funcionando en WSL2!"}

@app.post("/data")
def receive_data(
    data: SensorData,
    api_key: str = Security(verify_api_key)  # Autenticación requerida
):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sensor_data (sensor_id, value) VALUES (%s, %s)",
            (data.sensor_id, data.value)
        )
        conn.commit()
        logger.info(f"Datos guardados: {data}")
        return {"status": "éxito", "datos": data.dict()}
    except Exception as e:
        if conn:
            conn.rollback()
        error_msg = f"Error al guardar datos: {str(e)}"
        logger.error(error_msg)
        if SHOW_DB_ERRORS:
            raise HTTPException(status_code=500, detail=f"Error al guardar: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="No se pudieron guardar los datos")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.get("/data")
def get_all_data(
    sensor_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    api_key: str = Security(verify_api_key)  # Autenticación requerida
):
    conn = None
    cursor = None
    try:
        # Validar parámetros de paginación
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:  # Límite máximo por seguridad
            page_size = 100

        # Validar y parsear fechas
        from_dt = None
        to_dt = None
        if from_date:
            try:
                from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de from_date inválido. Use ISO 8601 (ej: 2025-04-05T10:30:00)")
        if to_date:
            try:
                to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de to_date inválido. Use ISO 8601 (ej: 2025-04-05T10:30:00)")

        # Construir consulta dinámicamente
        base_query = "SELECT * FROM sensor_data"
        conditions = []
        params = []

        if sensor_id:
            conditions.append("sensor_id = %s")
            params.append(sensor_id)

        if from_dt:
            conditions.append("timestamp >= %s")
            params.append(from_dt.strftime("%Y-%m-%d %H:%M:%S"))

        if to_dt:
            conditions.append("timestamp <= %s")
            params.append(to_dt.strftime("%Y-%m-%d %H:%M:%S"))

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        base_query += " ORDER BY timestamp DESC"

        # Calcular offset para paginación
        offset = (page - 1) * page_size
        paginated_query = base_query + " LIMIT %s OFFSET %s"
        params.extend([page_size, offset])

        # Ejecutar consulta
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(paginated_query, params)
        rows = cursor.fetchall()

        # Formatear los timestamps a ISO 8601 con 'Z'
        for row in rows:
            if 'timestamp' in row and row['timestamp']:
                row['timestamp'] = format_timestamp_to_iso_z(str(row['timestamp']))

        # Contar total (sin paginación) para metadatos
        count_query = "SELECT COUNT(*) as total FROM sensor_data"
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)
        cursor.execute(count_query, params[:-2])  # Excluye LIMIT y OFFSET
        total = cursor.fetchone()["total"]

        logger.info(f"Consulta: {len(rows)} registros devueltos (página {page}, tamaño {page_size})")
        return {
            "count": len(rows),
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
            "filters": {
                "sensor_id": sensor_id,
                "from_date": from_date,
                "to_date": to_date
            },
            "data": rows
        }

    except HTTPException:
        raise  # Re-lanzar errores HTTP explícitos
    except Exception as e:
        error_msg = f"Error al leer datos: {str(e)}"
        logger.error(error_msg)
        if SHOW_DB_ERRORS:
            raise HTTPException(status_code=500, detail=f"Error al leer: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Error al recuperar los datos")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
