import subprocess


class UserService:

    PASSWD_FILE = (
       "/etc/mosquitto/passwd" 
    )

    def create_user(
        self,
        username: str,
        password: str
    ):

        result = subprocess.run(
            [
                #"sudo",
                "mosquitto_passwd",
                "-b",
                self.PASSWD_FILE,
                username,
                password
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

    def list_users(self):

        users = []

        try:
            with open(
                self.PASSWD_FILE,
                "r"
            ) as file:

                for line in file:
                    if ":" in line:
                        users.append(
                            line.split(":")[0]
                        )

        except FileNotFoundError:
            return []

        return users
