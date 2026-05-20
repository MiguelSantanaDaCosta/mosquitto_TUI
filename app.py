import os
import sys
from ui.main_screen import MosquittoTUI

if __name__ == "__main__":
    # Verifica se o script está rodando como root (UID 0)
    if os.geteuid() != 0:
        print("🔑 Esta aplicação precisa de privilégios para gerenciar o Mosquitto.")
        
        # O os.execvp substitui o processo atual pelo comando sudo.
        # Usamos '-E' para preservar o ambiente Python (encontrando o Textual)
        # sys.executable é o caminho do Python atual
        # sys.argv são os argumentos que você passou pro script
        os.execvp("sudo", ["sudo", "-E", sys.executable] + sys.argv)

    # Se o código chegou até aqui, significa que a senha foi aceita
    # e o processo já é root. Agora podemos iniciar a TUI com segurança.
    app = MosquittoTUI()
    app.run()
