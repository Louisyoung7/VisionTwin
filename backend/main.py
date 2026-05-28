"""
VisionTwin 后端服务入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ws_endpoints import ws_vision, ws_frontend, _start_vehicle_cleanup
from api_routes import router as api_router
from mqtt_broker import start as mqtt_start
from db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    mqtt_start()
    _start_vehicle_cleanup()
    yield


app = FastAPI(title="VisionTwin", lifespan=lifespan)

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
