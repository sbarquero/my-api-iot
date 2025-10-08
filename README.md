# 🌐 API IoT para air12lite

API REST para recibir y servir datos de sensores IoT (como ESP32) con **FastAPI**, **MariaDB** y **Apache2** como proxy inverso.
Diseñada para desplegarse en **Ubuntu Server 22.04/24.04**.

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi)
![MariaDB](https://img.shields.io/badge/MariaDB-003545?style=flat&logo=mariadb)
![Apache](https://img.shields.io/badge/Apache-D22128?style=flat&logo=apache)
![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=flat&logo=ubuntu)

---

## 📦 Características

- ✅ Recepción de datos de sensores vía POST (`/data`)
- ✅ Consulta de datos con filtrado por `sensor_id`, fechas y paginación
- ✅ Validación automática con Pydantic
- ✅ Documentación interactiva en `/docs`
- ✅ Seguridad: usuario dedicado, sin exposición directa de Uvicorn
- ✅ Listo para producción: systemd + Apache2 proxy inverso

---

## 🚀 Despliegue en Ubuntu Server

### Requisitos previos

- Ubuntu Server 22.04 LTS o 24.04 LTS
- Acceso `sudo`
- Conexión a internet
- Nombre de host configurado como `air12lite` (opcional pero recomendado)

### 1. Clonar el repositorio

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/tu-usuario/my-api-iot.git
cd my-api-iot
```

### 2. Ejecutar el script de instalación

```bash
chmod +x deploy/install.sh
sudo ./deploy/install.sh
```

> ⏱️ El script instalará:
> - Python 3, pip, venv
> - Apache2 + módulos de proxy
> - MariaDB
> - Creará usuario `apiuser` y base de datos `sensor_db`
> - Configurará entorno virtual y dependencias
> - Iniciará el servicio systemd
> - Configurará Apache2 como proxy inverso

### 3. Configurar credenciales (opcional)

Si deseas usar contraseñas personalizadas:

```bash
sudo nano /opt/my-api-iot/app/.env
```

Actualiza:
```env
DB_PASSWORD=tu_contraseña_segura
```

Luego reinicia el servicio:
```bash
sudo systemctl restart my-api-iot
```

---

## 🔍 Comprobaciones

### Estado del servicio
```bash
sudo systemctl status my-api-iot
```

### Ver logs en tiempo real
```bash
sudo journalctl -u my-api-iot -f
```

### Pruebas locales
```bash
# Probar API
curl http://localhost

# Probar documentación
curl http://localhost/docs
```

### Acceso desde la red
Desde cualquier dispositivo en la misma red:
- http://air12lite
- http://air12lite/docs

> 💡 Asegúrate de que el nombre `air12lite` esté resuelto (IP fija en router o mDNS activado).

---

## 📡 Endpoints

### `POST /data`
Recibe datos de sensores.

**Ejemplo:**
```json
{
  "sensor_id": "esp32_temp",
  "value": 23.5
}
```

### `GET /data`
Obtiene datos con opciones de filtrado:

| Parámetro | Ejemplo | Descripción |
|----------|---------|-------------|
| `sensor_id` | `?sensor_id=temp1` | Filtra por ID de sensor |
| `from_date` | `?from_date=2025-04-05T10:00:00` | Desde esta fecha (ISO 8601) |
| `to_date` | `?to_date=2025-04-05T12:00:00` | Hasta esta fecha |
| `page` | `?page=2` | Página (por defecto: 1) |
| `page_size` | `?page_size=50` | Registros por página (máx: 100) |

**Respuesta:**
```json
{
  "count": 2,
  "total": 45,
  "page": 1,
  "page_size": 20,
  "pages": 3,
  "filters": { ... },
  "data": [ ... ]
}
```

---

## 🔄 Actualizaciones

Para actualizar la API después de cambios en el código:

```bash
cd my-api-iot
git pull origin main
sudo ./deploy/install.sh
```

> ✅ El script es **idempotente**: se puede ejecutar múltiples veces sin problemas.

---

## 🛡️ Seguridad

- **Usuario dedicado**: `apiuser` (sin privilegios de sistema)
- **Base de datos aislada**: solo acceso a `sensor_db`
- **Uvicorn no expuesto**: solo accesible desde localhost (Apache2 hace proxy)
- **Contraseñas fuera de Git**: usa `.env` en el servidor

---

## 📁 Estructura del proyecto

```
my-api-iot/
├── app/                    # Código fuente de FastAPI
│   ├── main.py
│   └── .env
├── venv/                   # Entorno virtual (no en Git)
├── requirements.txt        # Dependencias de Python
├── .env.example            # Plantilla de variables de entorno
├── deploy/
│   ├── install.sh          # Script de despliegue
│   ├── systemd/            # Archivo de servicio
│   └── apache2/            # Configuración de Apache2
└── README.md
```

---

## 📜 Licencia

Este proyecto es de código abierto bajo la Licencia MIT.
Ver [LICENSE](LICENSE) para más detalles.

---

## 🙌 Autor

- **Santiago Barquero**
- Repositorio: [https://github.com/sbarquero/my-api-iot](https://github.com/sbarquero/my-api-iot)
---

> 💡 **Consejo**: Para desarrollo local en WSL2, consulta la [guía de desarrollo](docs/development.md) (opcional).

---
