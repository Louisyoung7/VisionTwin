# VisionTwin 后端服务

智瞳云枢系统的后端服务，负责接收边缘检测模块(C4_stream)的车辆数据，并提供Web API和WebSocket通信。

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 完整功能启动
python main.py

# 禁用 MQTT (无甲烷传感器时使用)
python main.py --no-mqtt
```

### 3. 访问服务

- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--no-mqtt` | 禁用 MQTT 功能 (甲烷传感器不可用) |

## 配置

编辑 `backend/config.ini`:

```ini
[server]
host = 0.0.0.0
port = 8000

[mqtt]
host = localhost
port = 1883
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/vehicles` | 获取当前行驶车辆 |
| GET | `/api/vehicles/docked` | 获取停靠车辆 |
| GET | `/api/methane` | 获取甲烷传感器数据 |
| GET | `/api/alerts` | 获取告警列表 |
| GET | `/api/stats` | 获取统计数据 |

## WebSocket 端点

| 路径 | 说明 |
|------|------|
| `/ws/vision` | 接收C4_stream边缘检测模块推送的车辆数据 |
| `/ws` | 向前端推送实时车辆位置和告警信息 |

## 与 C4_stream 集成

C4_stream 检测到车辆数据后，通过 WebSocket 推送到本服务:

```python
# C4_stream 端
ws_pusher.push_frame_data(payload)
# payload 包含: track_id, plate, position, zones, compliance 等
```

VisionTwin 后端接收数据后在地图上可视化展示。
