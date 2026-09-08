"""
REST API 端点
"""
from datetime import datetime
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import JSONResponse

from db import (
    get_docked_vehicles, get_vehicle_score, get_all_vehicles,
    ensure_vehicle, update_vehicle_score, save_docked_vehicle,
    get_methane_history, get_score_change_history,
    get_alert_history, get_alert_stats
)
from mqtt_broker import publish_device_command, mqtt_sensors, mqtt_sensors_lock, DEVICE_IDS
from alerts import alerts, alerts_lock, generate_pothole_alert, IMAGE_SAVE_DIR
from ws_endpoints import get_current_vehicles, broadcast

router = APIRouter()

# frame_id → image_filename 映射（关联告警图片）
_pothole_images: dict[int, str] = {}


# ===== 甲烷传感器 =====

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


# ===== 车辆 =====

@router.get("/vehicles")
async def get_vehicles():
    """
    获取当前行驶中的所有车辆，每个车辆包含：
    plate, score, route_id, position, followed
    """
    current = get_current_vehicles()
    all_veh = get_all_vehicles()
    score_map = {v["plate"]: v["score"] for v in all_veh}

    result = []
    for plate, cv in current.items():
        result.append({
            "id": plate,
            "plate": plate,
            "status": "行驶",
            "score": score_map.get(plate, 100),
            "route_id": cv.get("route_id"),
            "position": cv.get("center", []),
            "followed": cv.get("followed", True)
        })

    return JSONResponse({"vehicles": result})


@router.get("/vehicles/docked")
async def get_docked_vehicles_api():
    """
    获取所有停靠车辆，每个车辆包含：
    plate, score
    """
    docked = get_docked_vehicles()
    all_veh = get_all_vehicles()
    score_map = {v["plate"]: v["score"] for v in all_veh}

    result = []
    for v in docked:
        result.append({
            "plate": v["plate"],
            "score": score_map.get(v["plate"], 100)
        })

    return JSONResponse({"docked_vehicles": result})


@router.get("/vehicles/{plate}/score")
async def get_vehicle_score_api(plate: str):
    score = get_vehicle_score(plate)
    if score is None:
        return JSONResponse({"error": "Vehicle not found"}, status_code=404)
    return JSONResponse({"plate": plate, "score": score})


@router.post("/vehicles/{plate}/score")
async def update_vehicle_score_api(plate: str, followed: bool):
    """更新车辆积分"""
    ensure_vehicle(plate)
    new_score = update_vehicle_score(plate, followed)
    return JSONResponse({"plate": plate, "score": new_score})


# ===== 告警 =====

@router.get("/alerts")
async def get_alerts():
    with alerts_lock:
        return JSONResponse({"alerts": list(alerts)})


@router.post("/alerts/{alert_id}/confirm")
async def confirm_alert(alert_id: int):
    """确认某条告警"""
    with alerts_lock:
        for i, a in enumerate(alerts):
            if a["id"] == alert_id:
                a["confirmed"] = True
                a["confirmed_time"] = a.get("time", "")
                return JSONResponse({"status": "ok", "alert": a})
    return JSONResponse({"error": "Alert not found"}, status_code=404)


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: int):
    """删除某条告警"""
    with alerts_lock:
        for i, a in enumerate(alerts):
            if a["id"] == alert_id:
                alerts.pop(i)
                return JSONResponse({"status": "ok"})
    return JSONResponse({"error": "Alert not found"}, status_code=404)


# ===== 设备控制 =====

@router.post("/device/{device_id}/command")
async def send_device_command_api(device_id: str, command: int):
    if device_id not in DEVICE_IDS:
        return JSONResponse({"error": f"device_id must be one of {DEVICE_IDS}"}, status_code=400)
    direction, topic = publish_device_command(device_id, command)
    return JSONResponse({"status": "ok", "device_id": device_id, "command": command, "direction": direction, "topic": topic})


# ===== 历史数据 =====

@router.get("/history/alerts")
async def get_history_alerts(source: str = None, level: str = None, hours: int = 24):
    """获取告警历史记录"""
    data = get_alert_history(source=source, level=level, hours=hours)
    return JSONResponse({"alerts": data})


@router.get("/history/methane")
async def get_history_methane(sensor_id: int | None = None, hours: int = 24):
    """获取甲烷浓度历史"""
    data = get_methane_history(sensor_id=sensor_id, hours=hours)
    return JSONResponse({"methane_history": data})


@router.get("/history/score")
async def get_history_score(plate: str = None, hours: int = 24):
    """获取积分变化历史"""
    data = get_score_change_history(plate=plate, hours=hours)
    return JSONResponse({"score_history": data})


@router.get("/history/stats")
async def get_history_stats(hours: int = 24):
    """获取统计数据"""
    data = get_alert_stats(hours=hours)
    return JSONResponse(data)


# ===== 车牌 OCR =====

@router.post("/ocr")
async def receive_ocr(plate_number: str = None, frame_id: int = 0):
    """
    接收车牌OCR识别结果（来自MaixCam）
    保存到停靠车辆表
    """
    from datetime import datetime
    if plate_number is None:
        return JSONResponse({"error": "plate_number is required"}, status_code=400)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[OCR] {timestamp} | {plate_number} | frame=#{frame_id}")

    save_docked_vehicle(plate_number)
    return JSONResponse({"status": "ok", "plate_number": plate_number})


# ===== 坑洼告警 =====

@router.post("/alert_json")
async def receive_alert_json(request: Request):
    """
    接收坑洼检测结果（JSON），关联图片后生成告警并推送给前端
    """
    try:
        body = await request.body()
        import json
        data = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    frame_id = data.get("frame_id", 0)
    image_filename = _pothole_images.pop(frame_id, None)

    alert = generate_pothole_alert(data, image_filename)
    if alert:
        await broadcast({"type": "alert", "alert": alert})

    detections = data.get("detections", [])
    total = data.get("total_count", len(detections))
    return JSONResponse({"status": "ok", "count": total})


@router.post("/alert_image")
async def receive_alert_image(file: UploadFile = File(...), frame_id: int = 0):
    """
    接收坑洼标注截图（JPEG），保存到 alerts/pothole_images/
    并记录 frame_id 与图片的关联
    """
    contents = await file.read()
    if not contents:
        return JSONResponse({"error": "Empty file"}, status_code=400)

    filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
    filepath = os.path.join(IMAGE_SAVE_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    if frame_id > 0:
        _pothole_images[frame_id] = filename

    print(f"[坑洼截图] {filename} ({len(contents)} bytes) frame=#{frame_id}")
    return JSONResponse({"status": "ok", "filename": filename})


@router.get("/history/pothole")
async def get_history_pothole(hours: int = 24):
    """获取坑洼检测历史"""
    from db import get_pothole_history
    data = get_pothole_history(hours=hours)
    return JSONResponse({"pothole_history": data})
