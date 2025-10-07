from fastapi import FastAPI, HTTPException
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

app = FastAPI(title="API IoT air12lite", description="Recibe y sirve datos de sensores")

# --- MODELO DE DATOS ---
class SensorData(BaseModel):
    sensor_id: str
    value: float

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

# --- ENDPOINTS ---
@app.get("/")
def read_root():
    return {"mensaje": "¡Servidor FastAPI + MariaDB funcionando en WSL2!"}

@app.post("/data")
def receive_data(data: SensorData):
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
    page_size: int = 20
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