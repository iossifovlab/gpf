import os
from datasets.default_settings import DATA_DIR

DATA_DIR = os.environ.get(
    "DATA_STUDIES_DIR",
    os.path.join(DATA_DIR, "study_groups")
)

CONFIG_FILE = os.environ.get(
    "DATA_STUDIES_CONF",
    "study_groups.conf"
)
