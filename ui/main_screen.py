from textual.app import (
    App,
    ComposeResult
)

from textual.containers import (
    Horizontal,
    Vertical
)

from textual.widgets import (
    Header,
    Footer,
    Button,
    Input,
    Label,
    Log,
    TabbedContent,
    TabPane
)

#from patterns.observer import Observer
from core.mqtt_manager import MQTTManager
from core.infra_service import InfraFacade
from core.systemd_service import SystemdService
from core.user_service import UserService
from core.telemetry_service import (
    TelemetryService
)
from ui.dynamic_tabs import (
    DynamicTabManager
)
from patterns.strategies import (
    PayloadParser
)


class MosquittoTUI(
    App,
    #Observer
):

    CSS = """
    Screen {
        background: #24273a;
    }

    TabbedContent {
        margin: 1;
    }

    Log {
        border: solid #8aadf4;
        height: 1fr;
    }

    Input {
        margin-bottom: 1;
    }

    Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear_logs", "Clear")
    ]

    def __init__(self):
        super().__init__()

        self.mqtt = MQTTManager()
        self.mqtt.register(self)

        self.infra = InfraFacade()
        self.systemd = (
            SystemdService()
        )

        self.user_service = (
            UserService()
        )

        self.telemetry = (
            TelemetryService()
        )

        self.dynamic_tabs = (
            DynamicTabManager()
        )

    def compose(
        self
    ) -> ComposeResult:

        yield Header(
            show_clock=True
        )

        with TabbedContent(
            id="tabs-main"
        ):

            with TabPane(
                "📊 Infraestrutura",
                id="tab-infra"
            ):
                yield Log(
                    id="log-infra"
                )

                yield Button(
                    "Atualizar",
                    id="btn-refresh"
                )

            with TabPane(
                "📡 MQTT",
                id="tab-mqtt"
            ):
                yield Log(
                    id="log-mqtt"
                )

            with TabPane(
                "📤 Publicar",
                id="tab-publish"
            ):
                yield Label(
                    "Tópico"
                )

                yield Input(
                    placeholder="sensores/temp",
                    id="input-topic"
                )

                yield Label(
                    "Payload"
                )

                yield Input(
                    placeholder='{"temp": 20}',
                    id="input-payload"
                )

                yield Button(
                    "Publicar",
                    id="btn-publish"
                )

                yield Log(
                    id="log-publish"
                )

            with TabPane(
                "⚙ Servidor",
                id="tab-server"
            ):

                with Horizontal():

                    yield Button(
                        "Start",
                        id="btn-start"
                    )

                    yield Button(
                        "Stop",
                        id="btn-stop"
                    )

                    yield Button(
                        "Restart",
                        id="btn-restart"
                    )

                    yield Button(
                        "Logs",
                        id="btn-logs"
                    )

                yield Log(
                    id="log-server"
                )

            with TabPane(
                "👥 Usuários",
                id="tab-users"
            ):

                yield Input(
                    placeholder="username",
                    id="input-user"
                )

                yield Input(
                    placeholder="password",
                    password=True,
                    id="input-password"
                )

                yield Button(
                    "Cadastrar",
                    id="btn-user"
                )

                yield Log(
                    id="log-users"
                )

        yield Footer()

    def on_mount(self):

        self.mqtt.connect()

        self.refresh_infra()

    def update(
        self,
        data
    ):
        self.call_from_thread(
            self.process_message,
            data
        )

    async def process_message(
        self,
        data
    ):
        topic = data["topic"]
        payload = data["payload"]
        timestamp = data[
            "timestamp"
        ]

        log = self.query_one(
            "#log-mqtt",
            Log
        )

        strategy = (
            PayloadParser
            .get_strategy(
                payload
            )
        )

        try:
            parsed = (
                strategy.parse(
                    payload
                )
            )

            log.write_line(
                f"[{timestamp}] "
                f"{topic} -> "
                f"{parsed}"
            )

        except Exception:
            log.write_line(
                f"[{timestamp}] "
                f"{topic} -> "
                f"{payload}"
            )

        tabs = self.query_one(
            "#tabs-main",
            TabbedContent
        )

        await (
            self.dynamic_tabs
            .create_topic_tab(
                tabs,
                topic
            )
        )

        safe_topic = (
            topic.replace(
                "/",
                "-"
            )
        )

        try:
            topic_log = (
                self.query_one(
                    f"#log-{safe_topic}",
                    Log
                )
            )

            topic_log.write_line(
                f"[{timestamp}] "
                f"{payload}"
            )

        except Exception:
            pass

    def on_button_pressed(
        self,
        event:
        Button.Pressed
    ):

        button_id = (
            event.button.id
        )

        if button_id == (
            "btn-publish"
        ):
            self.publish_message()

        elif button_id == (
            "btn-refresh"
        ):
            self.refresh_infra()

        elif button_id == (
            "btn-start"
        ):
            self.run_systemctl(
                "start"
            )

        elif button_id == (
            "btn-stop"
        ):
            self.run_systemctl(
                "stop"
            )

        elif button_id == (
            "btn-restart"
        ):
            self.run_systemctl(
                "restart"
            )

        elif button_id == (
            "btn-logs"
        ):
            self.load_logs()

        elif button_id == (
            "btn-user"
        ):
            self.create_user()

    def publish_message(
        self
    ):
        topic = (
            self.query_one(
                "#input-topic",
                Input
            ).value
        )

        payload = (
            self.query_one(
                "#input-payload",
                Input
            ).value
        )

        log = self.query_one(
            "#log-publish",
            Log
        )

        if not topic or not payload:
            log.write_line(
                "Topic/Payload inválido"
            )
            return

        self.mqtt.publish(
            topic,
            payload
        )

        log.write_line(
            f"Publicado: "
            f"{topic}"
        )

    def refresh_infra(
        self
    ):
        log = self.query_one(
            "#log-infra",
            Log
        )

        log.clear()

        telemetry = (
            self.telemetry
            .get_connection()
        )

        log.write_line(
            f"Conexões: "
            f"{telemetry['connections']}"
        )

        log.write(
            telemetry[
                "raw_output"
            ]
        )

    def run_systemctl(
        self,
        action
    ):
        log = self.query_one(
            "#log-server",
            Log
        )

        result = (
            self.systemd
            .execute(action)
        )

        if result[
            "success"
        ]:
            log.write_line(
                f"OK: {action}"
            )
        else:
            log.write_line(
                result[
                    "stderr"
                ]
            )

    def load_logs(
        self
    ):
        log = self.query_one(
            "#log-server",
            Log
        )

        log.clear()

        logs = (
            self.infra
            .get_logs()
        )

        log.write(logs)

    def create_user(
        self
    ):
        username = (
            self.query_one(
                "#input-user",
                Input
            ).value
        )

        password = (
            self.query_one(
                "#input-password",
                Input
            ).value
        )

        log = self.query_one(
            "#log-users",
            Log
        )

        result = (
            self.user_service
            .create_user(
                username,
                password
            )
        )

        if result[
            "success"
        ]:
            log.write_line(
                f"Usuário "
                f"{username} "
                f"criado."
            )
        else:
            log.write_line(
                result[
                    "stderr"
                ]
            )

    def action_clear_logs(
        self
    ):
        try:
            active_tab = (
                self.query_one(
                    "#tabs-main",
                    TabbedContent
                ).active
            )

            if active_tab:
                for log in (
                    self.query(
                        Log
                    )
                ):
                    log.clear()

        except Exception:
            pass
