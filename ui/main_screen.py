from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Button, Input, Label, TabbedContent, TabPane,
    Tree, Static, Log
)
from textual.widgets._tree import TreeNode

from core.mqtt_manager import MQTTManager
from core.infra_service import InfraFacade
from core.systemd_service import SystemdService
from core.user_service import UserService
from core.telemetry_service import TelemetryService
from core.utils import sanitize_topic_id, extract_numeric_values, format_payload, sparkline
from patterns.strategies import PayloadParser


class MosquittoTUI(App):
    CSS = """
    Screen {
        background: #000000;
    }
    TabbedContent {
        margin: 1;
    }
    Log {
        border: solid #4F4F4F;
    }
    Input {
        margin-bottom: 1;
    }
    Button {
        margin-right: 1;
    }
    #topic-tree {
        height: 1fr;
        border: solid #4F4F4F;
    }
    #search-input {
        margin: 0 0 1 0;
    }
    #status-bar {
        height: 1;
        padding: 0 1;
        background: #363a4f;
        color: #cad3f5;
    }
    #status-bar.connected {
        background: #a6da95;
        color: #24273a;
    }
    #status-bar.error {
        background: #ed8796;
        color: #24273a;
    }
    #status-bar.connecting {
        background: #eed49f;
        color: #24273a;
    }
    .mqtt-container {
        height: 1fr;
    }
    .tree-panel {
        width: 2fr;
        min-width: 30;
    }
    .detail-panel {
        width: 3fr;
        min-width: 40;
        padding: 0 0 0 1;
    }
    #detail-topic {
        background: #363a4f;
        color: #BC8F8F;
        text-style: bold;
        padding: 0 1;
        height: 1;
    }
    #detail-payload {
        border: solid #6c7086;
        height: 1fr;
        margin: 1 0 0 0;
        padding: 0 1;
    }
    #detail-graph {
        border: solid #6c7086;
        height: 3;
        margin: 1 0 0 0;
        padding: 0 1;
    }
    #detail-history {
        border: solid #6c7086;
        height: 1fr;
        margin: 1 0 0 0;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear_logs", "Clear"),
        ("f", "focus_search", "Search"),
        ("slash", "focus_search", "Search"),
    ]

    def __init__(self):
        super().__init__()
        self.mqtt = MQTTManager()
        self.mqtt.register(self)
        self.mqtt.on_state_change = self._on_mqtt_state

        self.infra = InfraFacade()
        self.systemd = SystemdService()
        self.user_service = UserService()
        self.telemetry = TelemetryService()

        self.topic_history: dict[str, list[dict]] = {}
        self.topic_nodes: dict[str, TreeNode] = {}
        self.selected_topic: str | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="status-bar")
        with TabbedContent(id="tabs-main"):
            with TabPane("Infraestrutura", id="tab-infra"):
                yield Log(id="log-infra")
                yield Button("Atualizar", id="btn-refresh")
            with TabPane("MQTT", id="tab-mqtt"):
                with Horizontal(classes="mqtt-container"):
                    with Vertical(classes="tree-panel"):
                        yield Input(placeholder="Buscar topico... (f ou /)", id="search-input")
                        yield Tree("Topicos", id="topic-tree")
                    with Vertical(classes="detail-panel"):
                        yield Static(id="detail-topic")
                        yield Static(id="detail-payload")
                        yield Static(id="detail-graph")
                        yield Log(id="detail-history", highlight=True)
            with TabPane("Publicar", id="tab-publish"):
                yield Label("Topico")
                yield Input(placeholder="sensores/temp", id="input-topic")
                yield Label("Payload")
                yield Input(placeholder='{"temp": 20}', id="input-payload")
                yield Button("Publicar", id="btn-publish")
                yield Log(id="log-publish")
            with TabPane("Servidor", id="tab-server"):
                with Horizontal():
                    yield Button("Start", id="btn-start")
                    yield Button("Stop", id="btn-stop")
                    yield Button("Restart", id="btn-restart")
                    yield Button("Logs", id="btn-logs")
                yield Log(id="log-server")
            with TabPane("Usuarios", id="tab-users"):
                yield Input(placeholder="username", id="input-user")
                yield Input(placeholder="password", password=True, id="input-password")
                yield Button("Cadastrar", id="btn-user")
                yield Log(id="log-users")
        yield Footer()

    def on_mount(self):
        self._update_status_bar(False, None)
        self.mqtt.connect()

    def _on_mqtt_state(self, connected, error):
        self.call_from_thread(self._update_status_bar, connected, error)

    def _update_status_bar(self, connected, error=None):
        try:
            bar = self.query_one("#status-bar", Static)
        except Exception:
            return
        classes = set()
        if connected:
            classes.add("connected")
            bar.update(" Conectado ao broker MQTT")
        elif error:
            classes.add("error")
            bar.update(f" Erro: {error}")
        else:
            classes.add("connecting")
            bar.update(" Conectando...")
        bar.set_classes(" ".join(sorted(classes)))

    def _ensure_topic_in_tree(self, topic: str) -> TreeNode | None:
        tree = self.query_one("#topic-tree", Tree)
        segments = topic.split("/")
        node: TreeNode = tree.root
        current_path: list[str] = []

        for i, segment in enumerate(segments):
            current_path.append(segment)
            full_path = "/".join(current_path)

            if full_path in self.topic_nodes:
                node = self.topic_nodes[full_path]
                continue

            found = None
            for child in node.children:
                if child.label == segment:
                    found = child
                    break
            if found:
                self.topic_nodes[full_path] = found
                node = found
                continue

            is_leaf = i == len(segments) - 1
            new_node = node.add(
                segment,
                data={"topic": topic} if is_leaf else {"topic": None}
            )
            self.topic_nodes[full_path] = new_node
            node = new_node

        return node

    def _expand_path(self, topic: str):
        segments = topic.split("/")
        current: list[str] = []
        for segment in segments:
            current.append(segment)
            path = "/".join(current)
            node = self.topic_nodes.get(path)
            if node:
                try:
                    node.expand()
                except Exception:
                    pass

    def _apply_search(self, query: str):
        q = query.strip().lower()
        if not q:
            for node in self.topic_nodes.values():
                try:
                    node.set_label(node.label)
                except Exception:
                    pass
            self._clear_search_markers()
            return

        matched_any = False
        for topic, node in self.topic_nodes.items():
            data = node.data
            if data and data.get("topic") and q in topic.lower():
                matched_any = True
                self._expand_path(topic)
                try:
                    node.set_label(f"[bold]{node.label}[/bold]")
                except Exception:
                    pass

        if not matched_any:
            bar = self.query_one("#status-bar", Static)
            bar.update(" Nenhum topico encontrado")

    def _clear_search_markers(self):
        for node in self.topic_nodes.values():
            try:
                label = node.label
                if isinstance(label, str) and "[/bold]" in label:
                    clean = label.replace("[bold]", "").replace("[/bold]", "")
                    node.set_label(clean)
            except Exception:
                pass

    def _update_detail_panel(self, topic: str):
        history = self.topic_history.get(topic, [])

        topic_widget = self.query_one("#detail-topic", Static)
        topic_widget.update(f"  {topic}  ({len(history)} msgs)")

        payload_widget = self.query_one("#detail-payload", Static)
        if history:
            latest = history[-1]
            formatted = format_payload(latest["payload"])
            payload_widget.update(formatted)
        else:
            payload_widget.update("(sem mensagens)")

        graph_widget = self.query_one("#detail-graph", Static)
        values: list[float] = []
        for entry in history[-200:]:
            values.extend(extract_numeric_values(entry["payload"]))
        if values:
            line = sparkline(values, 50)
            graph_widget.update(
                f"  {line}  min={min(values):.2f}  max={max(values):.2f}  "
                f"ultimo={values[-1]:.2f}"
            )
        else:
            graph_widget.update(" (sem dados numericos para grafico)")

        history_log = self.query_one("#detail-history", Log)
        history_log.clear()
        for entry in history[-200:]:
            history_log.write_line(
                f"[{entry['timestamp']}] {entry['payload']}"
            )

    def update(self, data):
        self.call_from_thread(self.process_message, data)

    async def process_message(self, data):
        topic = data["topic"]
        payload = data["payload"]
        timestamp = data["timestamp"]

        if topic not in self.topic_history:
            self.topic_history[topic] = []
        self.topic_history[topic].append(data)

        self._ensure_topic_in_tree(topic)

        log_mqtt = self.query_one("#log-mqtt", Log)
        strategy = PayloadParser.get_strategy(payload)
        try:
            parsed = strategy.parse(payload)
            log_mqtt.write_line(f"[{timestamp}] {topic} -> {parsed}")
        except Exception:
            log_mqtt.write_line(f"[{timestamp}] {topic} -> {payload}")

        if topic == self.selected_topic:
            self._update_detail_panel(topic)

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        data = event.node.data
        if data and data.get("topic"):
            self.selected_topic = data["topic"]
            self._update_detail_panel(self.selected_topic)

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "search-input":
            self._apply_search(event.value)

    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "btn-publish":
            self.publish_message()
        elif button_id == "btn-refresh":
            self.refresh_infra()
        elif button_id == "btn-start":
            self.run_systemctl("start")
        elif button_id == "btn-stop":
            self.run_systemctl("stop")
        elif button_id == "btn-restart":
            self.run_systemctl("restart")
        elif button_id == "btn-logs":
            self.load_logs()
        elif button_id == "btn-user":
            self.create_user()

    def publish_message(self):
        topic = self.query_one("#input-topic", Input).value
        payload = self.query_one("#input-payload", Input).value
        log = self.query_one("#log-publish", Log)
        if not topic or not payload:
            log.write_line("Topic/Payload invalido")
            return

        retain = False
        cfg = self.mqtt.config
        if cfg.get("tls_enabled"):
            pass

        self.mqtt.publish(topic, payload, retain=retain)
        log.write_line(f"Publicado: {topic}")

    def refresh_infra(self):
        log = self.query_one("#log-infra", Log)
        log.clear()
        telemetry = self.telemetry.get_connection()
        log.write_line(f"Conexoes: {telemetry['connections']}")
        log.write(telemetry["raw_output"])

    def run_systemctl(self, action):
        log = self.query_one("#log-server", Log)
        result = self.systemd.execute(action)
        if result["success"]:
            log.write_line(f"OK: {action}")
        else:
            log.write_line(result["stderr"])

    def load_logs(self):
        log = self.query_one("#log-server", Log)
        log.clear()
        logs = self.infra.get_logs()
        log.write(logs)

    def create_user(self):
        username = self.query_one("#input-user", Input).value
        password = self.query_one("#input-password", Input).value
        log = self.query_one("#log-users", Log)
        result = self.user_service.create_user(username, password)
        if result["success"]:
            log.write_line(f"Usuario {username} criado.")
        else:
            log.write_line(result["stderr"])

    def action_focus_search(self):
        try:
            self.query_one("#search-input", Input).focus()
        except Exception:
            pass

    def action_clear_logs(self):
        try:
            for log in self.query(Log):
                log.clear()
        except Exception:
            pass
