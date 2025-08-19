import gc
from contextlib import suppress
from typing import cast

import numpy as np
import tensorflow as tf
from pkg_resources import resource_filename


def spliceai_open() -> list:
    """Open SpliceAI annotator implementation."""
    physical_devices = tf.config.list_physical_devices("GPU")
    for device in physical_devices:
        with suppress(Exception):
            tf.config.experimental.set_memory_growth(
                device, enable=True)

    model_paths = [
        f"models/spliceai{i}.h5" for i in range(1, 6)
    ]
    return [
        tf.keras.models.load_model(
            resource_filename(__name__, path))
        for path in model_paths
    ]


def spliceai_close() -> None:
    tf.keras.backend.clear_session()
    gc.collect()


def spliceai_predict(
    models: list,
    x: np.ndarray,
) -> np.ndarray:
    return cast(np.ndarray, np.mean([
        models[m].predict(x, verbose=0)
        for m in range(5)
    ], axis=0))
