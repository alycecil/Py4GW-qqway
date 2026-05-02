import json

from types import SimpleNamespace

def dict_to_string(data):
    """
    Convert to a JSON string.
    Ensures non-ASCII characters are preserved.
    """
    return json.dumps(data, ensure_ascii=False)


def string_to_dict(data_str, default_value=None, object_hook=lambda d: SimpleNamespace(**d)):
    """
    Convert a JSON string back
    Includes error handling for invalid JSON.
    """
    if not isinstance(data_str, str):
        print("Input must be a string.")
        return default_value
    try:
        result = json.loads(data_str, object_hook=object_hook)
        return result
    except json.JSONDecodeError as e:
        print(f"Invalid JSON string: {e}")
        return default_value
