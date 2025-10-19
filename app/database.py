import mysql.connector
from mysql.connector import Error
from fastapi import HTTPException
import logging

from app.config import DB_NAME, DB_USER, DB_PASSWORD, SHOW_DB_ERRORS

logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return connection
    except Error as e:
        error_msg = f"Error al conectar con la base de datos: {str(e)}"
        logger.error(error_msg)
        if SHOW_DB_ERRORS:
            raise HTTPException(status_code=500, detail=f"Error DB: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Error interno del servidor")
