import os
import logging
from fastapi import FastAPI, Response, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from .mqtt_worker import (
    start_mqtt_worker,
    stop_mqtt_worker,
    get_mqtt_status,
    get_recent_events,
)

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Biến môi trường
SERVICE_NAME = os.getenv("SERVICE_NAME", "iot-ingestion")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    mqtt: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    logger.info("Starting IoT Ingestion Service for Demo Day...")
    start_mqtt_worker()
    yield
    # Shutdown event
    logger.info("Shutting down service...")
    stop_mqtt_worker()

app = FastAPI(
    title="FIT4110 Demo Day - IoT Ingestion Service",
    version=SERVICE_VERSION,
    description="IoT Ingestion API xử lý dữ liệu MQTT.",
    lifespan=lifespan
)

@app.get("/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    # Endpoint bắt buộc của Demo Day
    mqtt_status = get_mqtt_status()
    is_connected = mqtt_status.get("connected", False)
    
    if not is_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return HealthResponse(
        status="ok" if is_connected else "error",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        mqtt="connected" if is_connected else "disconnected"
    )


# ── Dashboard: hiển thị log thời gian thực + dữ liệu đẩy lên topic ───────────
_DASHBOARD_HTML = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    """Trang giám sát trực quan các event A1 publish lên topic."""
    return FileResponse(_DASHBOARD_HTML)


@app.get("/api/recent-events")
def recent_events():
    """Trả 50 event đã xử lý gần nhất + trạng thái MQTT (cho dashboard poll)."""
    return JSONResponse({
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "mqtt": "connected" if get_mqtt_status().get("connected") else "disconnected",
        "output_topic": os.getenv("MQTT_OUTPUT_TOPIC", "smart-campus/events/sensor"),
        "events": get_recent_events(),
    })