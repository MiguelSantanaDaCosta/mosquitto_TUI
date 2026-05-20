import paho.mqtt.client as mqtt
import threading
import time


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

        self.client = mqtt.Client(
            client_id="tui_admin"
        )

        self.observers = []

        self.client.on_message = (
            self.on_message
        )

        self.client.on_connect = (
            self.on_connect
        )

        self.running = False
        self._initialized = True

    def connect(
        self,
        host="127.0.0.1",
        port=1883
    ):
        self.running = True

        def worker():

            while self.running:

                try:
                    self.client.connect(
                        host,
                        port,
                        60
                    )

                    self.client.loop_forever()

                except Exception as e:
                    print(
                        f"MQTT Error: {e}"
                    )

                    time.sleep(2)

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def stop(self):
        self.running = False

        try:
            self.client.disconnect()
        except Exception:
            pass

    def subscribe(
        self,
        topic="#"
    ):
        self.client.subscribe(
            topic
        )

    def publish(
        self,
        topic,
        payload
    ):
        self.client.publish(
            topic,
            payload
        )

    def register(
        self,
        observer
    ):
        self.observers.append(
            observer
        )

    def notify(
        self,
        message
    ):
        for observer in self.observers:
            observer.update(
                message
            )

    def on_connect(
        self,
        client,
        userdata,
        flags,
        rc
    ):
        if rc == 0:
            self.subscribe("#")

    def on_message(
        self,
        client,
        userdata,
        msg
    ):
        try:
            payload = (
                msg.payload.decode(
                    "utf-8"
                )
            )

        except Exception:
            payload = str(
                msg.payload
            )

        data = {
            "topic":
                msg.topic,

            "payload":
                payload,

            "timestamp":
                time.strftime(
                    "%H:%M:%S"
                )
        }

        self.notify(
            data
        )
