import os
import threading
import time
import paho.mqtt.client as mqtt


ENV_MAP = {
    "host": ("MQTTUI_BROKER_HOST", "127.0.0.1"),
    "port": ("MQTTUI_BROKER_PORT", "1883"),
    "username": ("MQTTUI_USERNAME", None),
    "password": ("MQTTUI_PASSWORD", None),
    "client_id": ("MQTTUI_CLIENTID", "tui_admin"),
    "topic_filter": ("MQTTUI_TOPIC_FILTER", "#"),
    "tls_enabled": ("MQTTUI_TLS", "false"),
    "tls_ca_cert": ("MQTTUI_TLS_CA_CERT", None),
    "tls_cert": ("MQTTUI_TLS_CERT", None),
    "tls_key": ("MQTTUI_TLS_KEY", None),
    "tls_insecure": ("MQTTUI_TLS_INSECURE", "false"),
}


class MQTTManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.config = self._load_config()
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.config["client_id"],
            protocol=mqtt.MQTTv311
        )
        self.observers = []
        self.on_state_change = None
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.running = False
        self.connected = False
        self.last_error = None
        self._initialized = True

    def _load_config(self) -> dict:
        def env(key):
            var, default = ENV_MAP[key]
            val = os.environ.get(var)
            return val if val is not None else default

        port = int(env("port"))
        return {
            "host": env("host"),
            "port": port,
            "username": env("username"),
            "password": env("password"),
            "client_id": env("client_id"),
            "topic_filter": env("topic_filter"),
            "tls_enabled": env("tls_enabled").lower() == "true",
            "tls_ca_cert": env("tls_ca_cert"),
            "tls_cert": env("tls_cert"),
            "tls_key": env("tls_key"),
            "tls_insecure": env("tls_insecure").lower() == "true",
        }

    def _setup_tls(self):
        cfg = self.config
        if not cfg["tls_enabled"]:
            return
        ca_cert = cfg["tls_ca_cert"]
        cert = cfg["tls_cert"]
        key = cfg["tls_key"]
        if cert and key:
            if ca_cert:
                self.client.tls_set(ca_certs=ca_cert, certfile=cert, keyfile=key)
            else:
                self.client.tls_set(certfile=cert, keyfile=key)
        elif ca_cert:
            self.client.tls_set(ca_certs=ca_cert)
        else:
            self.client.tls_set()
        if cfg["tls_insecure"]:
            self.client.tls_insecure_set(True)

    def _notify_state(self):
        if self.on_state_change:
            try:
                self.on_state_change(self.connected, self.last_error)
            except Exception:
                pass

    def connect(self, host=None, port=None):
        cfg = self.config
        if host is not None:
            cfg["host"] = host
        if port is not None:
            cfg["port"] = port
        self.running = True
        self._setup_tls()
        if cfg["username"] and cfg["password"]:
            self.client.username_pw_set(cfg["username"], cfg["password"])

        def worker():
            while self.running:
                try:
                    self.last_error = None
                    self._notify_state()
                    self.client.connect(cfg["host"], cfg["port"], 60)
                    self.client.loop_forever()
                except Exception as e:
                    self.last_error = str(e)
                    self.connected = False
                    self._notify_state()
                    time.sleep(2)

        threading.Thread(target=worker, daemon=True).start()

    def stop(self):
        self.running = False
        self.connected = False
        try:
            self.client.disconnect()
        except Exception:
            pass

    def subscribe(self, topic=None):
        if topic is None:
            topic = self.config["topic_filter"]
        self.client.subscribe(topic)

    def publish(self, topic, payload, retain=False):
        self.client.publish(topic, payload, retain=retain)

    def register(self, observer):
        self.observers.append(observer)

    def notify(self, message):
        for observer in self.observers:
            try:
                observer.update(message)
            except Exception:
                pass

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.connected = True
            self.last_error = None
            self.subscribe()
        else:
            reasons = {
                1: "Conexão recusada: protocolo não compatível",
                2: "Conexão recusada: client-id inválido",
                3: "Conexão recusada: servidor indisponível",
                4: "Conexão recusada: usuário ou senha inválidos",
                5: "Conexão recusada: não autorizado",
            }
            self.last_error = reasons.get(reason_code, f"Erro de conexão: código {reason_code}")
        self._notify_state()

    def on_disconnect(self, client, userdata, reason_code, properties):
        self.connected = False
        if reason_code != 0:
            self.last_error = "Conexão perdida com o broker"
        else:
            self.last_error = None
        self._notify_state()

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
        except Exception:
            payload = str(msg.payload)
        data = {
            "topic": msg.topic,
            "payload": payload,
            "timestamp": time.strftime("%H:%M:%S"),
            "retain": msg.retain,
            "qos": msg.qos,
        }
        self.notify(data)
