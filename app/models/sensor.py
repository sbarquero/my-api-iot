from pydantic import BaseModel

class SensorData(BaseModel):
    sensor_id: str
    value: float
