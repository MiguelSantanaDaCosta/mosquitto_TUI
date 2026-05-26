import subprocess


class InfraFacade:

    def get_connection(self, port=1883):
        result = subprocess.run(
            ["ss", "-t", "-a", f"sport = :{port} or dport = :{port}"],
            capture_output=True, text=True
        )
        return result.stdout

    def get_logs(self):
        result = subprocess.run(
            ["journalctl", "-u", "mosquitto", "-n", "20", "--no-pager"],
            capture_output=True, text=True
        )
        return result.stdout
