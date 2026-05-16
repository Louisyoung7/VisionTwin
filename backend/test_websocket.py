# 用于测试 WebSocket 连通性

import websocket
import json

def on_message(ws, message):
    print("Received:", json.loads(message))

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    # 发送视频路径（后端会接收但暂时忽略）
    ws.send("test_video.mp4")
    print("Sent video path: test_video.mp4")

if __name__ == "__main__":
    # WebSocket 连接地址
    ws_url = "ws://127.0.0.1:8000/ws"
    websocket.enableTrace(True)
    
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # 运行 WebSocket 客户端
    ws.run_forever()