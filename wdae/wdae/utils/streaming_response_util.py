import json
import numpy as np


def convert(obj):
    if isinstance(obj, np.int64):
        return int(obj)
    elif isinstance(obj, np.float32):
        return float(obj)
    else:
        raise TypeError(
            "Unserializable object {} of type {}".format(obj, type(obj))
        )


def iterator_to_json(variants):
    for v in variants:
        yield json.dumps(v, default=convert)
