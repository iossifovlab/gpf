import os

DATA_DIR = os.environ.get(
    "DAE_DATA_DIR",
    '.'
)

DATA_DATASETS_DIR = os.environ.get(
    "DATA_DATASETS_DIR",
    "{}/datasets".format(DATA_DIR)
)
