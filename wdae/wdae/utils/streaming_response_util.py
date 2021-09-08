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
    try:
        yield "["
        curr = next(variants, None)
        post = next(variants, None)
        while curr is not None:
            yieldval = json.dumps(curr, default=convert)
            if post is None:
                yield yieldval
                break
            else:
                yield yieldval + ","
            curr = post
            post = next(variants, None)
        yield "]"
        return 0
    except GeneratorExit:
        # TODO
        print("Iterator closed!")
