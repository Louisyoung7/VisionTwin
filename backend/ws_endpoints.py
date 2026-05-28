"""
WebSocket 端点 - 视觉模块数据接收 + 前端实时推送
"""
import asyncio
import json
import threading
import time
from fastapi import WebSocket

from db import ensure_vehicle, delete_vehicle

vehicles: dict[int, dict] = {}
vehicles_lock = threading.Lock()
vehicle_last_seen: dict[int, float] = {}
VEHICLE_TIMEOUT = 60.0

frontend_clients: set[WebSocket] = set()
frontend_clients_lock = threading.Lock()


async def ws_vision(websocket: WebSocket):
    """接收视觉模块推送的车辆数据"""
    await websocket.accept()
    print("[WebSocket] 视觉模块已连接")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                vehicle_list = payload.get("vehicles", [])

                with vehicles_lock:
                    now = time.time()
                    for v in vehicle_list:
                        vid = v.get("id")
                        if vid is not None:
                            vehicles[vid] = v
                            vehicle_last_seen[vid] = now
                            ensure_vehicle(vid)

                await _broadcast_vehicles(vehicle_list)

            except json.JSONDecodeError:
                print(f"[WebSocket] 解析视觉数据失败: {data[:100]}")

    except Exception as e:
        print(f"[WebSocket] 视觉模块连接异常: {e}")
    finally:
        print("[WebSocket] 视觉模块已断开")


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


async def _broadcast_vehicles(vehicle_list: list):
    """广播车辆数据给所有前端客户端"""
    with frontend_clients_lock:
        dead_clients = set()
        for client in frontend_clients:
            try:
                await client.send_json({"vehicles": vehicle_list})
            except Exception:
                dead_clients.add(client)
        for dead in dead_clients:
            frontend_clients.discard(dead)


async def broadcast_score_change(vehicle_id: int, score: int):
    """广播积分变更事件（ET 模式）"""
    event = {
        "type": "score_change",
        "vehicle_id": vehicle_id,
        "score": score
    }
    with frontend_clients_lock:
        dead_clients = set()
        for client in frontend_clients:
            try:
                await client.send_json(event)
            except Exception:
                dead_clients.add(client)
        for dead in dead_clients:
            frontend_clients.discard(dead)
    print(f"[WebSocket 广播] 车辆 #{vehicle_id} 积分变化 → {score}")


def _start_vehicle_cleanup():
    """后台线程：每 30 秒清理超 60 秒无更新的车辆"""
    def run():
        while True:
            time.sleep(30)
            now = time.time()
            with vehicles_lock:
                stale = [vid for vid, t in vehicle_last_seen.items() if now - t > VEHICLE_TIMEOUT]
                for vid in stale:
                    vehicles.pop(vid, None)
                    vehicle_last_seen.pop(vid, None)
                    delete_vehicle(vid)
                    print(f"[车辆清理] 车辆 #{vid} 超时移除（数据库同步删除）")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
