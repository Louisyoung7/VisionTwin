from fastapi import FastAPI, WebSocket
import asyncio
import random

app = FastAPI()

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.receive_text()  # 接收任意启动信号
    
    while True:
        # 生成 Mock 3D 位置数据（模拟 YOLO 输出）
        data = {
            "objects": [
                {
                    "id": 1,
                    "type": "person",
                    "position": [  # 随机 3D 坐标 (x, y, z)
                        round(random.uniform(-5, 5), 2),
                        0.0,  # 地面高度
                        round(random.uniform(-5, 5), 2)
                    ]
                }
            ]
        }
        await websocket.send_json(data)
        await asyncio.sleep(0.1)  # 10fps