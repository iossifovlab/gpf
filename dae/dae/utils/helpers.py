import os
import math
import numpy as np
from box import Box  # type: ignore


def study_id_from_path(filepath):
    return os.path.splitext(os.path.basename(filepath))[0]


def str2bool(value):
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return value.lower() in {"true", "yes", "1", "1.0", "t", "y"}


def isnan(val):
    return val is None or np.isnan(val)


def camelize_string(data: str) -> str:
    tokens = data.split('_')
    return tokens[0] + ''.join(x.title() for x in tokens[1:])


def to_response_json(data) -> dict:
    """Converts a dict or Box to an acceptable response JSON."""
    result: dict = dict()

    for key, value in data.items():
        if isinstance(value, Box):
            value = value.to_dict()

        if isinstance(value, dict):
            result[camelize_string(key)] = to_response_json(value)
        elif isinstance(value, list) or isinstance(value, tuple):
            new_value = list()
            for item in value:
                if isinstance(item, dict):
                    new_value.append(to_response_json(item))
                else:
                    new_value.append(item)
            result[camelize_string(key)] = new_value
        else:
            result[camelize_string(key)] = value
    return result


def convert_size(size_bytes: int) -> str:
    """
    Convert an integer representing size in bytes to a human-readable string.

    Copied from https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
    """
    if size_bytes == 0:
        return "0B"
    suffix = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    exponent = int(math.floor(math.log(size_bytes, 1024)))
    size = round(size_bytes / math.pow(1024, exponent), 2)
    return f"{size} {suffix[exponent]}"
