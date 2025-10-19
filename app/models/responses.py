from pydantic import BaseModel

class SensorDataResponse(BaseModel):
    id: int
    sensor_id: str
    value: float
    timestamp: str  # Devolverá formato ISO 8601 con 'Z'