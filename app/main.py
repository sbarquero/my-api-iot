from fastapi import FastAPI

from app.api.v1 import sensor_data
from app.security import verify_api_key, security

app = FastAPI(title="API IoT", description="Recibe y sirve datos de sensores")

# Incluir routers
app.include_router(sensor_data.router)

@app.get("/")
def read_root():
    return {"mensaje": "¡Servidor FastAPI + MariaDB funcionando en WSL2!"}