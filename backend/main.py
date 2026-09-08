"""
VisionTwin 后端服务入口
"""
import os
import argparse
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ws_endpoints import ws_vision, ws_frontend
from api_routes import router as api_router
from mqtt_broker import start as mqtt_start
from db import init_db
from alerts import ALERT_SAVE_DIR
from config import SERVER_HOST, SERVER_PORT


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if not getattr(app.state, "skip_mqtt", False):
        mqtt_start()
    yield


app = FastAPI(title="VisionTwin", lifespan=lifespan)
app.state.skip_mqtt = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.websocket("/ws/vision")(ws_vision)
app.websocket("/ws")(ws_frontend)

# 静态文件：坑洼截图
os.makedirs(ALERT_SAVE_DIR, exist_ok=True)
app.mount("/alerts", StaticFiles(directory=ALERT_SAVE_DIR), name="alerts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VisionTwin 后端服务")
    parser.add_argument("--no-mqtt", action="store_true", help="禁用 MQTT 功能")
    args = parser.parse_args()

    if args.no_mqtt:
        app.state.skip_mqtt = True
        print("MQTT 功能已禁用")

    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="error")
