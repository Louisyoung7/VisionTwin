import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws/yolo")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        video_path = await websocket.receive_text()
        print(f"Received video path: {video_path}")
        
        # 读取 mock 数据（后续替换为 YOLO 调用）
        mock_file = Path("mock_data/frame_001.json")
        if not mock_file.exists():
            await websocket.send_json({"error": "Mock data file not found"})
            return
        
        with open(mock_file) as f:
            data = json.load(f)
        
        # 持续发送同一帧（模拟实时流）
        while True:
            await websocket.send_json(data)
            await asyncio.sleep(0.1)  # 10fps
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close(code=1011, reason=str(e))