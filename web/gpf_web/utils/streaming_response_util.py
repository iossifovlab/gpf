from __future__ import annotations

import json
import logging
from collections.abc import Generator
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def convert(obj: Any) -> int | float:
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    raise TypeError(
        f"Unserializable object {obj} of type {type(obj)}",
    )


def iterator_to_json(
    variants: Generator[list[Any] | None, None, None],
) -> Generator[str, None, None]:
    """Convert an iterator of dictionaries to a JSON array string generator."""
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
        logger.exception("unexpected exception")
    finally:
        variants.close()
        yield "]"
