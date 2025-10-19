from datetime import datetime

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