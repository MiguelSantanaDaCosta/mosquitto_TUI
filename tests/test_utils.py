from core.utils import (
    sanitize_topic_id,
    extract_numeric_values,
    format_payload,
    sparkline,
)


class TestSanitizeTopicId:
    def test_basic_topic(self):
        assert sanitize_topic_id("sensors/temp") == "sensors-temp"

    def test_mixed_chars(self):
        assert sanitize_topic_id("a/b/c") == "a-b-c"

    def test_special_chars(self):
        assert sanitize_topic_id("foo bar+baz#") == "foo-bar-baz-"


class TestExtractNumericValues:
    def test_plain_number(self):
        assert extract_numeric_values("25.5") == [25.5]

    def test_json_number(self):
        assert extract_numeric_values('{"temp": 25.5}') == [25.5]

    def test_json_multiple_values(self):
        result = extract_numeric_values('{"a": 1, "b": 2}')
        assert result == [1.0, 2.0]

    def test_non_numeric(self):
        assert extract_numeric_values("hello world") == []

    def test_mixed_text(self):
        result = extract_numeric_values("temp=25.5C humidity=60%")
        assert 25.5 in result
        assert 60.0 in result


class TestFormatPayload:
    def test_plain_text(self):
        assert format_payload("hello") == "hello"

    def test_json_pretty(self):
        result = format_payload('{"a": 1, "b": 2}')
        assert "{" in result
        assert '"a": 1' in result
        assert '"b": 2' in result

    def test_nested_json(self):
        result = format_payload('{"x": {"y": [1, 2, 3]}}')
        assert '"x"' in result
        assert '"y"' in result


class TestSparkline:
    def test_empty(self):
        assert sparkline([]) == ""

    def test_single_value(self):
        result = sparkline([42.0], width=5)
        assert len(result) > 0

    def test_min_max(self):
        result = sparkline([0.0, 100.0], width=2)
        assert result[0] != result[1]  # different characters

    def test_all_same(self):
        result = sparkline([50.0, 50.0, 50.0], width=3)
        assert all(c == result[0] for c in result)
