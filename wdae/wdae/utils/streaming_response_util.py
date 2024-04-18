import json
import logging

import numpy as np

logger = logging.getLogger(__name__)


def convert(obj):
    if isinstance(obj, np.int64):
        return int(obj)
    if isinstance(obj, np.float32):
        return float(obj)
    raise TypeError(
        f"Unserializable object {obj} of type {type(obj)}",
    )


def iterator_to_json(variants):

    try:
        yield "["
        curr = next(variants)
        while curr is None:
            yield ""
            curr = next(variants)
        yield json.dumps(curr, default=convert, allow_nan=False)

        while True:

            curr = next(variants)
            while curr is None:
                yield ""
                curr = next(variants)

            yield ","
            yield json.dumps(curr, default=convert, allow_nan=False)

    except StopIteration:
        logger.debug("iterator_to_json generator done")
    except GeneratorExit:
        logger.info("iterator_to_json generator closed")
    except BaseException:
        logger.exception("unexpected exception", exc_info=True)
    finally:
        variants.close()
        yield "]"
