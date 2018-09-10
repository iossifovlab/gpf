import os
from studies.default_settings import DATA_DIR

CONFIG_FILE = os.environ.get(
    "DATA_STUDIES_CONF",
    "study_groups.conf"
)
