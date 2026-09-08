"""配置加载 - 从 config.ini 读取"""
import configparser
import os

_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
_config = configparser.ConfigParser()
_config.read(_CONFIG_FILE, encoding="utf-8")

# Server
SERVER_HOST = _config.get("server", "host", fallback="127.0.0.1")
SERVER_PORT = _config.getint("server", "port", fallback=8000)

# MQTT
MQTT_HOST = _config.get("mqtt", "host", fallback="127.0.0.1")
MQTT_PORT = _config.getint("mqtt", "port", fallback=1883)

# Log
LOG_METHANE_SENSOR = _config.getboolean("log", "methane_sensor", fallback=True)
