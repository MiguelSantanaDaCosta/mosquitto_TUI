import json
import re


def sanitize_topic_id(topic: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", topic)


def sparkline(values: list[float], width: int = 40) -> str:
    if not values:
        return ""
    if len(values) == 1:
        values = values * 2
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return "\u2581" * min(width, len(values))
    chars = "\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
    step = (max_val - min_val) / (len(chars) - 1)
    result = []
    sampled = values[::max(1, len(values) // width)][:width]
    for v in sampled:
        idx = int((v - min_val) / step) if step > 0 else 0
        idx = min(idx, len(chars) - 1)
        result.append(chars[idx])
    return "".join(result)


def extract_numeric_values(payload: str) -> list[float]:
    values = []
    try:
        data = json.loads(payload)
        if isinstance(data, (int, float)):
            values.append(float(data))
        elif isinstance(data, dict):
            for v in data.values():
                if isinstance(v, (int, float)):
                    values.append(float(v))
        elif isinstance(data, list):
            for v in data:
                if isinstance(v, (int, float)):
                    values.append(float(v))
        return values
    except (json.JSONDecodeError, ValueError):
        pass
    for match in re.finditer(r'-?\d+\.?\d*(?:[eE][+-]?\d+)?', payload):
        values.append(float(match.group()))
    return values


def format_payload(payload: str) -> str:
    try:
        parsed = json.loads(payload)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, ValueError):
        return payload
