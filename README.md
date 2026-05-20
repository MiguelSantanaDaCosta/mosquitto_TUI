# Mosquitto TUI

[![License: GPL-2.0](https://img.shields.io/badge/License-GPL--2.0-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-green.svg)]()

**Mosquitto TUI** é uma interface de terminal para administração e monitoramento do broker MQTT Eclipse Mosquitto em ambientes Linux. A aplicação centraliza tarefas operacionais em uma única interface baseada em texto, reduzindo a dependência de múltiplos comandos do sistema e oferecendo uma experiência mais objetiva para administradores e desenvolvedores. [file:1]

---

## Visão geral

O projeto foi desenvolvido para facilitar o gerenciamento do Mosquitto diretamente no terminal, com foco em produtividade, clareza e modularidade. A solução combina utilitários nativos do Linux com uma interface construída em **Textual**, permitindo interação responsiva e organizada por áreas funcionais. [file:1]

A arquitetura foi estruturada para manter separação clara entre interface, serviços de sistema, comunicação MQTT e padrões de projeto. Esse desenho favorece manutenção, evolução incremental e ampliação futura das funcionalidades. [file:1]

---

## Principais recursos

- Controle do serviço Mosquitto via `systemd`.
- Exibição de logs recentes do `journald`.
- Monitoramento de conexões ativas na porta MQTT padrão.
- Criação de usuários com `mosquitto_passwd`.
- Publicação de mensagens MQTT diretamente pela interface.
- Recebimento e visualização em tempo real de mensagens por tópico.
- Criação dinâmica de abas conforme novos tópicos são identificados.
- Interpretação automática de payloads em JSON ou texto simples. [file:1]

---

## Requisitos

O projeto depende de um ambiente Linux com `systemd` e dos binários utilizados para administração do serviço e coleta de dados do sistema. [file:1]

### Dependências do sistema

- `systemctl`
- `journalctl`
- `ss`
- `mosquitto_passwd` [file:1]

### Dependências Python

- Python 3.10 ou superior.
- `textual`
- `paho-mqtt` [file:1]

---

## Estrutura do projeto

A organização do código segue uma separação por responsabilidade, com módulos dedicados a cada domínio funcional. [file:1]

### Core

- `core/infraservice.py`: coleta dados de infraestrutura e logs do Mosquitto.
- `core/systemdservice.py`: execução de operações sobre o serviço.
- `core/userservice.py`: gerenciamento de credenciais MQTT.
- `core/telemetryservice.py`: leitura de conexões estabelecidas.
- `core/mqttmanager.py`: gerenciamento da conexão MQTT e propagação de eventos. [file:1]

### Patterns

- `patterns/observer.py`: contrato para observadores.
- `patterns/commands.py`: encapsulamento de ações de sistema.
- `patterns/factory.py`: criação dinâmica de elementos da interface.
- `patterns/strategies.py`: definição da estratégia de parsing de payload. [file:1]

### UI

- `ui/widgets.py`: componentes reutilizáveis.
- `ui/dynamictabs.py`: gestão dinâmica das abas de tópicos.
- `ui/mainscreen.py`: tela principal da aplicação. [file:1]

### Models

- `models/message.py`: estrutura de mensagem MQTT. [file:1]

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/mosquitto-tui.git
cd mosquitto-tui
```

### 2. Crie o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

---

## Execução

A aplicação exige privilégios administrativos para interagir com o serviço Mosquitto e com o arquivo de credenciais. O ponto de entrada do projeto verifica se o processo já está executando como root e, caso necessário, reinicia a aplicação com `sudo -E`, preservando o ambiente do usuário. [file:1]

```bash
sudo -E venv/bin/python app.py
```

---

## Arquitetura

O projeto adota padrões de projeto para manter o código desacoplado e fácil de evoluir. [file:1]

- **Singleton**: garante uma única instância do `MQTTManager`.
- **Observer**: notifica a interface sempre que novas mensagens chegam.
- **Command**: encapsula ações relacionadas ao `systemctl`.
- **Factory Method**: cria abas de tópicos dinamicamente.
- **Strategy**: define o tratamento de payloads conforme o formato recebido. [file:1]

Essa abordagem torna o sistema mais previsível, especialmente em cenários com mensagens MQTT em fluxo contínuo e múltiplas interações administrativas. [file:1]

---

## Interface

A interface principal é dividida em abas que organizam as funções por contexto operacional. [file:1]

### Infraestrutura
Exibe telemetria de conexões e logs recentes do serviço Mosquitto, com opção de atualização manual. [file:1]

### MQTT
Mostra mensagens recebidas em tempo real e cria abas automaticamente para tópicos distintos. [file:1]

### Publicação
Permite publicar mensagens em qualquer tópico configurado, informando tópico e payload. [file:1]

### Servidor
Disponibiliza ações administrativas para controle do serviço Mosquitto e carregamento de logs. [file:1]

### Usuários
Permite cadastrar novos usuários MQTT com autenticação baseada em arquivo de senhas. [file:1]

---

## Licença

Este projeto é distribuído sob a licença **GPL-2.0**. Consulte o arquivo `LICENSE` para os termos completos. [file:1]

---

## Contribuição

Contribuições são bem-vindas por meio de issues e pull requests. Recomenda-se manter o padrão arquitetural existente e preservar a separação entre interface, serviços e lógica de domínio. [file:1]
