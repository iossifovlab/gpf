import os
from datasets.default_settings import DATA_DIR

DATA_DIR = os.environ.get(
    "DATA_STUDIES_DIR",
    os.path.join(DATA_DIR, "studies")
)

CONFIG_FILE = os.environ.get(
    "DATA_STUDIES_CONF",
    "studies.conf"
)

COMMON_REPORTS_DIR = os.environ.get(
    "DATA_STUDIES_COMMON_REPORTS_DIR",
    os.path.join(DATA_DIR, "commonReports")
)
