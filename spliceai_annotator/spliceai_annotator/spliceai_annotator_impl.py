import gc
from typing import cast

import numpy as np
import tensorflow as tf
from pkg_resources import resource_filename


def spliceai_load_models() -> list:
    """Open SpliceAI annotator implementation."""
    model_paths = [
        f"models/spliceai{i}.h5" for i in range(1, 6)
    ]
    return [
        tf.keras.models.load_model(
            resource_filename(__name__, path))
        for path in model_paths
    ]


def spliceai_close() -> None:
    gc.collect()


def spliceai_predict(
    models: list,
    x: np.ndarray,
) -> np.ndarray:
    return cast(np.ndarray, np.mean([
        models[m].predict(x, verbose=0)
        for m in range(5)
    ], axis=0))


SPLICEAI_MODELS = spliceai_load_models()
