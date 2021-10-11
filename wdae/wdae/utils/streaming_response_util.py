import json
import logging
import numpy as np


logger = logging.getLogger(__name__)


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
        curr = next(variants)
        while curr is None:
            yield ""
            curr = next(variants)
        yield json.dumps(curr, default=convert)

        while True:

            curr = next(variants)
            while curr is None:
                yield ""
                curr = next(variants)

            yield ","
            yield json.dumps(curr, default=convert)

    except StopIteration:
        logger.debug("iterator_to_json generator done")
    except GeneratorExit:
        logger.info("iterator_to_json generator closed")
    except BaseException:
        logger.exception("unexpected exception", exc_info=True)
    finally:
        variants.close()
        yield "]"
