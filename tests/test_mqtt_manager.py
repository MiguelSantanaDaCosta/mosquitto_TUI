import os
from unittest.mock import patch, MagicMock
from core.mqtt_manager import MQTTManager, ENV_MAP


class TestMQTTManagerConfig:
    def setup_method(self):
        # Reset singleton between tests
        MQTTManager._instance = None

    def test_default_config(self):
        manager = MQTTManager()
        assert manager.config["host"] == "127.0.0.1"
        assert manager.config["port"] == 1883
        assert manager.config["client_id"] == "tui_admin"
        assert manager.config["topic_filter"] == "#"
        assert manager.config["tls_enabled"] is False

    def test_env_config(self):
        MQTTManager._instance = None
        env = {
            "MQTTUI_BROKER_HOST": "10.0.0.1",
            "MQTTUI_BROKER_PORT": "8883",
            "MQTTUI_USERNAME": "admin",
            "MQTTUI_PASSWORD": "secret",
            "MQTTUI_CLIENTID": "test-client",
            "MQTTUI_TOPIC_FILTER": "sensors/#",
            "MQTTUI_TLS": "true",
        }
        with patch.dict(os.environ, env, clear=False):
            manager = MQTTManager()
            assert manager.config["host"] == "10.0.0.1"
            assert manager.config["port"] == 8883
            assert manager.config["username"] == "admin"
            assert manager.config["password"] == "secret"
            assert manager.config["client_id"] == "test-client"
            assert manager.config["topic_filter"] == "sensors/#"
            assert manager.config["tls_enabled"] is True


class TestMQTTManagerObserver:
    def setup_method(self):
        MQTTManager._instance = None

    def test_notify_calls_observers(self):
        manager = MQTTManager()
        mock = MagicMock()
        manager.register(mock)
        msg = {"topic": "test", "payload": "hello", "timestamp": "12:00:00"}
        manager.notify(msg)
        mock.update.assert_called_once_with(msg)

    def test_notify_multiple_observers(self):
        manager = MQTTManager()
        mocks = [MagicMock(), MagicMock()]
        for m in mocks:
            manager.register(m)
        msg = {"topic": "test"}
        manager.notify(msg)
        for m in mocks:
            m.update.assert_called_once_with(msg)

    def test_observer_exception_does_not_block(self):
        manager = MQTTManager()
        failing = MagicMock()
        failing.update.side_effect = Exception("fail")
        working = MagicMock()
        manager.register(failing)
        manager.register(working)
        manager.notify({"topic": "test"})
        working.update.assert_called_once()
