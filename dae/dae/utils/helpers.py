import os
import numpy as np


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
