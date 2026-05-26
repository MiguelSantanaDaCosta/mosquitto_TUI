import os
import sys

from ui.main_screen import MosquittoTUI

if __name__ == "__main__":

    in_docker = os.path.exists("/.dockerenv")

    if os.geteuid() != 0 and not in_docker:
        print("🔑 Esta aplicação precisa de privilégios para gerenciar o Mosquitto.")

        os.execvp(
            "sudo",
            ["sudo", "-E", sys.executable] + sys.argv
        )

    app = MosquittoTUI()
    app.run()
