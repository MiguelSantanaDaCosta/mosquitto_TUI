from abc import (
    ABC,
    abstractmethod
)
import subprocess


class Command(ABC):

    @abstractmethod
    def execute(self):
        pass


class StartMosquitto(Command):

    def execute(self):
        subprocess.run(
            [
                "systemctl",
                "start",
                "mosquitto"
            ]
        )


class StopMosquitto(Command):

    def execute(self):
        subprocess.run(
            [
                "systemctl",
                "stop",
                "mosquitto"
            ]
        )


class RestartMosquitto(
    Command
):

    def execute(self):
        subprocess.run(
            [
                "systemctl",
                "restart",
                "mosquitto"
            ]
        )


        

