from dataclasses import dataclass


@dataclass
class MQTTMessage:
    topic: str
    payload: str
    timestamp: str
