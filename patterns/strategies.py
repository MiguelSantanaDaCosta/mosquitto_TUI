import json
from abc import (
    ABC,
    abstractmethod
)


class PayloadStrategy(ABC):

    @abstractmethod
    def parse(self, payload):
        pass


class JsonStrategy(PayloadStrategy):

    def parse(self, payload):
        return json.loads(payload)


class TextStrategy(PayloadStrategy):

    def parse(self, payload):
        return payload


class PayloadParser:

    @staticmethod
    def get_strategy(payload):

        if payload.strip().startswith(
            ("{", "[")
        ):
            return JsonStrategy()

        return TextStrategy()
