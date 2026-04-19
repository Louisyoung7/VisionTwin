import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

from services.mock_yolo import MockYOLO

app = FastAPI()

@app.websocket("/ws/yolo")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        video_path = await websocket.receive_text()
        print(f"Received video path: {video_path}")

        mock_yolo = MockYOLO()
        
        async for frame_data in mock_yolo.process_video(video_path):
            await websocket.send_json(frame_data)
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close(code=1011, reason=str(e))