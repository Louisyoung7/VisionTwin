import json
import threading
from typing import Callable, Optional, List
import paho.mqtt.client as mqtt


class MQTTClient:
    def __init__(self, client_id: str = "", host: str = "localhost", port: int = 1883, username: str = "", password: str = ""):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id or f"mqtt_client_{id(self)}"
        self._client = mqtt.Client(client_id=self.client_id)
        self._subscriptions: List[tuple[str, int]] = []
        self._callbacks: dict[str, Callable[[str, bytes], None]] = {}
        self._lock = threading.Lock()
        self._connected = False
        self._connect_event = threading.Event()

        if username:
            self._client.username_pw_set(username, password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            self._connect_event.set()
            with self._lock:
                for topic, qos in self._subscriptions:
                    self._client.subscribe(topic, qos)
        else:
            self._connected = False
            self._connect_event.clear()

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        self._connect_event.clear()

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload
        with self._lock:
            if topic in self._callbacks:
                try:
                    self._callbacks[topic](topic, payload)
                except Exception as e:
                    print(f"MQTT callback error for topic '{topic}': {e}")

    def connect(self, timeout: float = 5.0) -> bool:
        try:
            self._client.connect(self.host, self.port, keepalive=60)
            self._client.loop_start()
            return self._connect_event.wait(timeout)
        except Exception as e:
            print(f"MQTT connect error: {e}")
            return False

    def disconnect(self):
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def publish(self, topic: str, payload: str | bytes | dict, qos: int = 0, retain: bool = False) -> int:
        if not self._connected:
            return -1

        if isinstance(payload, dict):
            payload = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, str):
            payload = payload.encode("utf-8")

        return self._client.publish(topic, payload, qos, retain)

    def subscribe(self, topic: str, callback: Callable[[str, bytes], None], qos: int = 0):
        with self._lock:
            self._callbacks[topic] = callback
            if self._connected:
                self._client.subscribe(topic, qos)
            self._subscriptions.append((topic, qos))

    def unsubscribe(self, topic: str):
        with self._lock:
            if topic in self._callbacks:
                del self._callbacks[topic]
            if self._connected:
                self._client.unsubscribe(topic)
            self._subscriptions = [(t, q) for t, q in self._subscriptions if t != topic]


class MQTTManager:
    _instance: Optional["MQTTManager"] = None

    def __init__(self):
        self._clients: dict[str, MQTTClient] = {}
        self._default_client: Optional[MQTTClient] = None

    @classmethod
    def get_instance(cls) -> "MQTTManager":
        if cls._instance is None:
            cls._instance = MQTTManager()
        return cls._instance

    def create_client(self, name: str, host: str = "localhost", port: int = 1883, username: str = "", password: str = "") -> MQTTClient:
        client = MQTTClient(
            client_id=f"{name}_{id(self)}",
            host=host,
            port=port,
            username=username,
            password=password
        )
        self._clients[name] = client
        return client

    def get_client(self, name: str) -> Optional[MQTTClient]:
        return self._clients.get(name)

    def set_default(self, name: str) -> bool:
        client = self._clients.get(name)
        if client:
            self._default_client = client
            return True
        return False

    def get_default(self) -> Optional[MQTTClient]:
        return self._default_client

    def publish(self, topic: str, payload: str | bytes | dict, qos: int = 0, retain: bool = False, client_name: str = "default") -> int:
        if client_name == "default":
            client = self._default_client
        else:
            client = self._clients.get(client_name)

        if not client:
            return -1
        return client.publish(topic, payload, qos, retain)

    def subscribe(self, topic: str, callback: Callable[[str, bytes], None], qos: int = 0, client_name: str = "default"):
        if client_name == "default":
            client = self._default_client
        else:
            client = self._clients.get(client_name)

        if client:
            client.subscribe(topic, callback, qos)

    def disconnect_all(self):
        for client in self._clients.values():
            client.disconnect()
        self._clients.clear()
        self._default_client = None


mqtt_manager = MQTTManager.get_instance()
