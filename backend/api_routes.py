"""
REST API 端点
"""
import time
from fastapi import APIRouter, WebSocket
from fastapi.responses import JSONResponse

from db import update_vehicle_score, get_vehicle_score, ensure_vehicle
from mqtt_broker import publish_device_command, mqtt_sensors, mqtt_sensors_lock, NUM_DEVICES
from alerts import alerts, alerts_lock
from ws_endpoints import vehicles, vehicles_lock, broadcast_score_change

router = APIRouter()


@router.get("/vehicles")
async def get_vehicles():
    with vehicles_lock:
        vehicle_list = list(vehicles.values())
    return JSONResponse({"vehicles": vehicle_list})


@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: int):
    with vehicles_lock:
        vehicle = vehicles.get(vehicle_id)
    if vehicle is None:
        return JSONResponse({"error": "Vehicle not found"}, status_code=404)
    return JSONResponse(vehicle)


@router.get("/methane")
async def get_methane():
    with mqtt_sensors_lock:
        sensor_list = list(mqtt_sensors.values())
    return JSONResponse({"methane": sensor_list})


@router.get("/methane/{sensor_id}")
async def get_methane_sensor(sensor_id: int):
    with mqtt_sensors_lock:
        sensor = mqtt_sensors.get(sensor_id)
    if sensor is None:
        return JSONResponse({"error": "Sensor not found"}, status_code=404)
    return JSONResponse(sensor)


@router.get("/alerts")
async def get_alerts():
    with alerts_lock:
        return JSONResponse({"alerts": list(alerts)})


@router.post("/device/{device_id}/command")
async def send_device_command_api(device_id: int, command: int):
    if not (0 <= device_id < NUM_DEVICES):
        return JSONResponse({"error": f"device_id must be 0 ~ {NUM_DEVICES - 1}"}, status_code=400)
    direction, topic = publish_device_command(device_id, command)
    return JSONResponse({"status": "ok", "device_id": device_id, "command": command, "direction": direction, "topic": topic})


@router.post("/vehicle/{vehicle_id}/route-feedback")
async def vehicle_route_feedback(vehicle_id: int, followed: bool):
    ensure_vehicle(vehicle_id)
    new_score = update_vehicle_score(vehicle_id, followed)
    if new_score is None:
        return JSONResponse({"error": "Vehicle not found"}, status_code=404)

    if not followed:
        await broadcast_score_change(vehicle_id, new_score)

    return JSONResponse({
        "vehicle_id": vehicle_id,
        "followed": followed,
        "score": new_score
    })


@router.get("/vehicle/{vehicle_id}/score")
async def get_vehicle_score_api(vehicle_id: int):
    score = get_vehicle_score(vehicle_id)
    if score is None:
        return JSONResponse({"error": "Vehicle not found"}, status_code=404)
    return JSONResponse({"vehicle_id": vehicle_id, "score": score})
