import os


DATA_DIR = os.environ.get(
    "DAE_DATA_DIR",
    "/home/lubo/Work/seq-pipeline/data-raw-dev/"
)

DATA_DATASETS_DIR = os.environ.get(
    "DATA_DATASETS_DIR",
    "{}/datasets".format(DATA_DIR)
)
