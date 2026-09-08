"""
车牌 OCR 模拟器 - 独立进程运行
模拟 MaixCam 设备识别到车牌后通过 REST API 向后台发送 OCR 结果

用法:
  python ocr_simulator.py                              # 默认5秒间隔
  python ocr_simulator.py --interval 3                 # 3秒间隔
  python ocr_simulator.py --plates 京A12345 沪B67890   # 指定车牌池
  python ocr_simulator.py --host 192.168.1.100         # 指定后端地址
"""
import argparse
import json
import random
import signal
import sys
import os
import time
import urllib.request
import urllib.parse
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import SERVER_HOST, SERVER_PORT

PROVINCES = list("京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁")
LETTERS = list("ABCDEFGHJKLMNPQRSTUVWXYZ")
DIGITS = list("0123456789")

DEFAULT_PLATES = [
    "京A12345", "京B67890", "沪A11111", "沪B22222",
    "粤A33333", "粤B44444", "苏A55555", "苏B66666",
    "浙A77777", "浙B88888", "鲁A99999", "鲁B00000",
]


def generate_plate():
    province = random.choice(PROVINCES)
    letter = random.choice(LETTERS)
    if random.random() < 0.5:
        tail = "".join(random.choices(DIGITS, k=5))
    else:
        tail = (
            random.choice(DIGITS + LETTERS)
            + random.choice(DIGITS + LETTERS)
            + "".join(random.choices(DIGITS, k=3))
        )
    return f"{province}{letter}{tail}"


class OcrSimulator:
    def __init__(self, interval=5, host="127.0.0.1", port=8000, plates=None):
        self.interval = interval
        self.host = host
        self.port = port
        self.plate_pool = plates or DEFAULT_PLATES[:]
        self.frame_id = 0
        self.running = False

    def _pick_plate(self):
        if random.random() < 0.7:
            return random.choice(self.plate_pool)
        return generate_plate()

    def _send(self, plate):
        url = f"http://{self.host}:{self.port}/api/ocr"
        params = urllib.parse.urlencode({"plate_number": plate, "frame_id": self.frame_id})
        try:
            req = urllib.request.Request(f"{url}?{params}", method="POST", data=b"")
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = json.loads(resp.read().decode())
                print(f"[✓] {plate} | frame=#{self.frame_id} | {body.get('status', '?')}")
        except urllib.error.URLError as e:
            print(f"[✗] {plate} | 连接失败: {e.reason}")
        except Exception as e:
            print(f"[✗] {plate} | 错误: {e}")

    def run(self):
        self.running = True
        print("=" * 40)
        print("  车牌 OCR 模拟器")
        print(f"  间隔: {self.interval}s")
        print(f"  后端: http://{self.host}:{self.port}")
        print(f"  车牌池: {len(self.plate_pool)} 个")
        print("=" * 40)
        print("\n按 Ctrl+C 停止\n")

        try:
            while self.running:
                plate = self._pick_plate()
                self.frame_id += 1
                self._send(plate)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n[停止] 收到中断信号")
        print("[停止] 模拟器已退出")

    def stop(self):
        self.running = False


def main():
    parser = argparse.ArgumentParser(description="车牌 OCR 模拟器")
    parser.add_argument("--interval", type=float, default=5,
                        help="发送间隔秒数 (默认: 5)")
    parser.add_argument("--host", default=SERVER_HOST,
                        help=f"后端地址 (默认: {SERVER_HOST})")
    parser.add_argument("--port", type=int, default=SERVER_PORT,
                        help=f"后端端口 (默认: {SERVER_PORT})")
    parser.add_argument("--plates", nargs="+", default=None,
                        help="指定车牌池，不指定则使用默认+随机生成")
    args = parser.parse_args()

    sim = OcrSimulator(
        interval=args.interval,
        host=args.host,
        port=args.port,
        plates=args.plates,
    )

    signal.signal(signal.SIGINT, lambda *_: sim.stop())
    signal.signal(signal.SIGTERM, lambda *_: sim.stop())

    sim.run()


if __name__ == "__main__":
    main()