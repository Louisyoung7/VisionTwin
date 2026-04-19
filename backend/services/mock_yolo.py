import asyncio
import random

class MockYOLO:
    def __init__(self, classes=["person", "car", "truck"]):
        self.classes = classes
    
    async def process_video(self, video_path: str):
        """模拟 YOLO 逐帧输出"""
        frame_id = 0
        while True:
            # 随机生成 0-3 个检测框
            objects = []
            for _ in range(random.randint(0, 3)):
                cls = random.choice(self.classes)
                # 随机 bbox (归一化坐标)
                x1, y1 = random.random(), random.random()
                x2, y2 = min(x1 + 0.2, 1.0), min(y1 + 0.3, 1.0)
                objects.append({
                    "class_name": cls,
                    "bbox": [x1, y1, x2, y2]
                })
            
            yield {
                "frame_id": frame_id,
                "timestamp": asyncio.get_event_loop().time(),
                "objects": objects
            }
            
            frame_id += 1
            await asyncio.sleep(0.1)  # 控制帧率