"""
WebSocket 端点 - 视觉模块数据接收 + 前端实时推送
"""
import json
import threading
from fastapi import WebSocket

from db import (
    ensure_vehicle, update_vehicle_score,
    save_docked_vehicle, remove_docked_vehicle,
    get_vehicle_score, save_score_change
)
from alerts import generate_vehicle_alert
from config import LOG_METHANE_SENSOR

# ============================================================
# 坐标系配置
# SVG 地图尺寸 (floot.svg: 502x636)
# 注意：坐标转换已在 C4_stream 端通过透视变换完成，
# 后端直接使用推送过来的 SVG 坐标，无需再做线性缩放。
# ============================================================
SVG_WIDTH = 502
SVG_HEIGHT = 636


# 当前行驶车辆: {track_id: {plate, camera_id, route_id, compliance, center, zones, violations}}
current_vehicles: dict[int, dict] = {}
current_vehicles_lock = threading.Lock()

# 本次运行中已扣过分的车辆（违规只扣一次）
_penalized_vehicles: set[str] = set()

# 导出给 api_routes 使用
def get_current_vehicles():
    with current_vehicles_lock:
        return {str(k): v for k, v in current_vehicles.items()}

frontend_clients: set[WebSocket] = set()
frontend_clients_lock = threading.Lock()


async def ws_vision(websocket: WebSocket):
    """接收视觉模块推送的行驶车辆数据
    新数据格式 (data.json):
    {
        "type": "vehicle_detect",
        "timestamp": "...",
        "frame_idx": 1842,
        "camera_id": "192.168.31.201",
        "vehicle_count": 2,
        "vehicles": [
            {
                "track_id": 3,
                "class_name": "car",
                "confidence": 0.87,
                "bbox": [x, y, w, h],
                "center": [cx, cy],
                "plate_number": "京A12345",
                "current_zones": [2],
                "path_compliance": {
                    "status": "compliant" | "violation",
                    "expected_zone": 3,
                    "visited_zones": [1, 2],
                    "progress": "2/4",
                    "violations": [
                        {"type": "wrong_order", "zone": 3, "description": "..."}
                    ]
                }
            }
        ]
    }
    """
    await websocket.accept()
    # 重连时清空已扣分记录和当前车辆（跨视频不重复扣）
    global _penalized_vehicles
    _penalized_vehicles = set()
    with current_vehicles_lock:
        current_vehicles.clear()
    print("[WebSocket] 视觉模块已连接（已清空状态）")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                msg_type = payload.get("type", "")

                # 心跳忽略
                if msg_type == "heartbeat":
                    continue

                # 车辆检测数据（按帧批量推送）
                if msg_type == "vehicle_detect":
                    frame_idx = payload.get("frame_idx", 0)
                    camera_id = payload.get("camera_id", "")
                    video_width = payload.get("video_width")
                    video_height = payload.get("video_height")
                    vehicles = payload.get("vehicles", [])
                    print(f"[WebSocket] 帧=#{frame_idx} 摄像头={camera_id} 车辆数={len(vehicles)} 视频={video_width}x{video_height}")

                    for v in vehicles:
                        # 调试：打印每辆车的 path_compliance 状态
                        pc = v.get("path_compliance", {})
                        pc_status = pc.get("status", "无")
                        if pc_status == "violation":
                            print(f"[DEBUG WS] track_id={v.get('track_id')} plate={v.get('plate_number')} compliance={pc_status}")
                        try:
                            await process_vehicle(camera_id, v, video_width, video_height)
                        except Exception as ve:
                            print(f"[WebSocket] 处理车辆异常: track_id={v.get('track_id')} plate={v.get('plate_number')} 错误={ve}")
                            import traceback
                            traceback.print_exc()
                            continue

                # 旧格式兼容：车辆停止
                elif msg_type == "vehicle_stopped":
                    plate = payload.get("plate")
                    if plate:
                        await handle_vehicle_stopped(plate)
                    continue

                # 旧格式兼容：车辆开始行驶
                elif msg_type == "vehicle_started":
                    plate = payload.get("plate")
                    if plate:
                        await handle_vehicle_started(
                            plate,
                            payload.get("route_id"),
                            payload.get("position", []),
                            payload.get("followed", True)
                        )
                    continue

                # 默认旧格式行驶数据更新（兼容）
                else:
                    plate = payload.get("plate")
                    if plate:
                        await handle_moving_update(
                            plate,
                            payload.get("route_id"),
                            payload.get("followed", True),
                            payload.get("position", []),
                            payload.get("violations", [])
                        )

            except json.JSONDecodeError:
                print(f"[WebSocket] 解析失败: {data[:100]}")

    except Exception as e:
        print(f"[WebSocket] 视觉模块连接异常: {e}")
    finally:
        print("[WebSocket] 视觉模块已断开")


async def process_vehicle(camera_id: str, vehicle: dict, video_width: int = None, video_height: int = None):
    """处理单个车辆检测数据"""
    track_id = vehicle.get("track_id")
    plate = vehicle.get("plate_number", "")
    center = vehicle.get("center", [])
    zones = vehicle.get("current_zones", [])
    compliance = vehicle.get("path_compliance", {})
    compliance_status = compliance.get("status", "无")
    violations = compliance.get("violations", [])
    route_id = compliance.get("expected_zone")  # 期望区域作为 route_id

    # 调试日志：每辆车都打印状态
    print(f"[process_vehicle] track={track_id} plate={plate!r} compliance_status={compliance_status!r} violations={violations}")

    # "unknown" 状态不视为违规，仅显式 "violation" 才扣分
    is_followed = compliance_status != "violation"

    # 没有车牌则用 track_id 标识
    if not plate:
        plate = f"track_{track_id}"

    # 坐标转换：视频像素 -> SVG 地图坐标 (已在C4_stream端完成透视变换)
    svg_center = center

    # 调试日志：确认违规状态是否正确传递
    if compliance_status == "violation":
        print(f"[DEBUG 违规] plate={plate} status={compliance_status} violations={violations}")

    # 确保数据库记录存在
    ensure_vehicle(plate)

    # 积分处理：违规只扣一次（用 plate 作为唯一标识）
    old_score = get_vehicle_score(plate) or 100
    if not is_followed:
        if plate not in _penalized_vehicles:
            _penalized_vehicles.add(plate)
            new_score = update_vehicle_score(plate, False)
            reason = violations[0].get("description", "路径违规") if violations else "状态更新"
            save_score_change(plate, old_score, new_score, reason)
            print(f"[积分] ★ {plate} {old_score} → {new_score}  原因: {reason}")
            await broadcast_score_change(plate, new_score)
        else:
            # 已扣过，不重复扣
            new_score = old_score
    else:
        new_score = old_score

    # 从停靠表移除（如有）
    remove_docked_vehicle(plate)

    # 更新内存中的当前车辆状态
    with current_vehicles_lock:
        current_vehicles[track_id] = {
            "track_id": track_id,
            "plate": plate,
            "camera_id": camera_id,
            "route_id": route_id,
            "compliance": compliance_status,
            "center": svg_center,
            "zones": zones,
            "violations": violations,
            "score": new_score
        }

    # 路径违规 → 生成告警
    if not is_followed:
        violation_msgs = []
        for v in violations:
            vtype = v.get("type", "unknown")
            desc = v.get("description", "")
            violation_msgs.append(f"[{vtype}] {desc}")

        alert = generate_vehicle_alert(
            plate=plate,
            level="warning",
            followed=False,
            location=svg_center,
            route_id=route_id
        )
        if alert:
            # 补充违规详情
            alert["violations"] = violations
            alert["track_id"] = track_id
            alert["camera_id"] = camera_id
            alert["message"] = f"路径违规: {'; '.join(violation_msgs) if violation_msgs else '未按规定路线行驶'}"
            await _broadcast({"type": "alert", "alert": alert})

    # 广播给前端（同时推送车辆数据和合规状态）
    await _broadcast_moving_vehicle(track_id, plate, camera_id, route_id, svg_center, zones, new_score, is_followed, compliance)


async def handle_vehicle_stopped(plate: str):
    """处理车辆停止事件（旧格式兼容）"""
    # 从当前行驶车辆中移除（遍历找 plate）
    with current_vehicles_lock:
        for tid, v in list(current_vehicles.items()):
            if v.get("plate") == plate:
                del current_vehicles[tid]
                break

    save_docked_vehicle(plate)
    await _broadcast({"type": "vehicle_stopped", "plate": plate})
    print(f"[WebSocket] 车辆 {plate} 停止行驶，已转为停靠")


async def handle_vehicle_started(plate: str, route_id, position: list, followed: bool):
    """处理车辆开始行驶事件（旧格式兼容）"""
    ensure_vehicle(plate)
    remove_docked_vehicle(plate)
    old_score = get_vehicle_score(plate) or 100
    new_score = update_vehicle_score(plate, followed)

    if new_score != old_score:
        save_score_change(plate, old_score, new_score, "状态更新")
        await broadcast_score_change(plate, new_score)

    # 坐标已在 C4_stream 端完成透视变换，直接使用
    svg_position = position

    with current_vehicles_lock:
        # 用 plate 作为 key（旧格式无 track_id）
        current_vehicles[id(plate)] = {
            "track_id": None,
            "plate": plate,
            "camera_id": "",
            "route_id": route_id,
            "compliance": "compliant" if followed else "violation",
            "center": svg_position,
            "zones": [],
            "violations": [],
            "score": new_score
        }

    await _broadcast_moving_vehicle(None, plate, "", route_id, svg_position, [], new_score, followed, None)
    print(f"[WebSocket] 车辆 {plate} 开始行驶")


async def handle_moving_update(plate: str, route_id, followed: bool, position: list, violations: list):
    """处理行驶数据更新（旧格式兼容）"""
    old_score = get_vehicle_score(plate) or 100
    new_score = update_vehicle_score(plate, followed)

    if new_score != old_score:
        reason = violations[0].get("description") if violations else "状态更新"
        save_score_change(plate, old_score, new_score, reason)
        await broadcast_score_change(plate, new_score)

    remove_docked_vehicle(plate)

    # 坐标已在 C4_stream 端完成透视变换，直接使用
    svg_position = position

    with current_vehicles_lock:
        current_vehicles[id(plate)] = {
            "track_id": None,
            "plate": plate,
            "camera_id": "",
            "route_id": route_id,
            "compliance": "compliant" if followed else "violation",
            "center": svg_position,
            "zones": [],
            "violations": violations,
            "score": new_score
        }

    if not followed:
        alert = generate_vehicle_alert(plate=plate, level="warning", followed=False,
                                       location=svg_position, route_id=route_id)
        if alert:
            alert["violations"] = violations
            await _broadcast({"type": "alert", "alert": alert})

    await _broadcast_moving_vehicle(None, plate, "", route_id, svg_position, [], new_score, followed, None)


async def ws_frontend(websocket: WebSocket):
    """前端 WebSocket 客户端连接"""
    await websocket.accept()
    print("[WebSocket] 前端客户端已连接")
    with frontend_clients_lock:
        frontend_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        with frontend_clients_lock:
            frontend_clients.discard(websocket)
        print("[WebSocket] 前端客户端已断开")


async def _broadcast_moving_vehicle(track_id, plate: str, camera_id: str, route_id,
                                     center: list, zones: list, score: int,
                                     followed: bool, compliance: dict):
    """广播行驶车辆数据给所有前端客户端"""
    event = {
        "type": "moving_vehicle",
        "track_id": track_id,
        "plate": plate,
        "camera_id": camera_id,
        "route_id": route_id,
        "position": center,
        "zones": zones,
        "score": score,
        "followed": followed,
        "compliance": compliance
    }
    await _broadcast(event)


async def _broadcast(event: dict):
    """广播事件给所有前端客户端"""
    with frontend_clients_lock:
        dead_clients = set()
        for client in frontend_clients:
            try:
                await client.send_json(event)
            except Exception:
                dead_clients.add(client)
        for dead in dead_clients:
            frontend_clients.discard(dead)


# 导出供 api_routes 调用
async def broadcast(event: dict):
    await _broadcast(event)


async def broadcast_score_change(plate: str, score: int):
    """广播积分变更事件"""
    await _broadcast({
        "type": "score_change",
        "plate": plate,
        "score": score
    })


def broadcast_methane_sensor(sensor_id: str, methane_pct: float, location: list, alert_level: str = None):
    """从非 async 上下文广播气体传感器数据（如 MQTT 回调线程）"""
    import asyncio
    event = {
        "type": "methane_sensor",
        "sensor_id": sensor_id,
        "methane_percentage": round(methane_pct, 2),
        "location": location,
        "alert_level": alert_level  # None=正常, "warning"=预警, "danger"=危险
    }
    try:
        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(_broadcast(event), loop)
    except RuntimeError:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(_broadcast(event), loop)
            else:
                loop.run_until_complete(_broadcast(event))
        except Exception:
            pass
    if LOG_METHANE_SENSOR:
        print(f"[WebSocket 广播] 气体传感器 sensor={sensor_id} 甲烷={methane_pct:.2f}% alert={alert_level}")


broadcast_alert_sync_lock = threading.Lock()


def broadcast_alert_sync(alert: dict):
    """从非 async 上下文广播告警（如 MQTT 回调线程）"""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(_broadcast({"type": "alert", "alert": alert}), loop)
    except RuntimeError:
        # 没有运行中的事件循环，尝试获取或创建
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(_broadcast({"type": "alert", "alert": alert}), loop)
            else:
                loop.run_until_complete(_broadcast({"type": "alert", "alert": alert}))
        except Exception:
            pass
    sensor_id = alert.get("sensor_id", "?")
    level = alert.get("level", "?")
    print(f"[WebSocket 广播] 甲烷告警 sensor={sensor_id} level={level}")
