from patterns.strategies import PayloadParser


class TestPayloadParser:
    def test_json_detection(self):
        strategy = PayloadParser.get_strategy('{"temp": 25}')
        parsed = strategy.parse('{"temp": 25}')
        assert parsed == {"temp": 25}

    def test_array_detection(self):
        strategy = PayloadParser.get_strategy("[1, 2, 3]")
        parsed = strategy.parse("[1, 2, 3]")
        assert parsed == [1, 2, 3]

    def test_text_fallback(self):
        strategy = PayloadParser.get_strategy("hello world")
        parsed = strategy.parse("hello world")
        assert parsed == "hello world"

    def test_numeric_string(self):
        strategy = PayloadParser.get_strategy("42")
        parsed = strategy.parse("42")
        assert parsed == "42"
