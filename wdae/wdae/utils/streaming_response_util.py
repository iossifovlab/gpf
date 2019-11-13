import json
import numpy as np


def convert(o):
    if isinstance(o, np.int64):
        return int(o)
    raise TypeError


def iterator_to_json(variants):
    for v in variants:
        yield json.dumps(v, default=convert)
