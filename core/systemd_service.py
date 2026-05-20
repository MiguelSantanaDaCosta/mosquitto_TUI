import subprocess


class SystemdService:

    def execute(
        self,
        action: str
    ):
        valid_actions = {
            "start",
            "stop",
            "restart",
            "reload",
            "reload-or-restart",
            "status"
        }

        if action not in valid_actions:
            raise ValueError(
                f"Ação inválida: {action}"
            )

        result = subprocess.run(
            [   
                #"sudo",
                "systemctl",
                action,
                "mosquitto"
            ],
            capture_output=True,
            text=True
        )

        return {
            "success":
                result.returncode == 0,
            "stdout":
                result.stdout,
            "stderr":
                result.stderr
        }
