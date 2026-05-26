import subprocess


class TelemetryService:

    def get_connection(self, port=1883):
        result = subprocess.run(
            ["ss", "-t", "-a", f"sport = :{port} or dport = :{port}"],
            capture_output=True, text=True
        )
        established = 0
        for line in result.stdout.splitlines():
            if "ESTAB" in line:
                established += 1
        return {
            "connections": established,
            "raw_output": result.stdout
        }
