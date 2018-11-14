import os
from datasets.default_settings import DATA_DIR

DATA_DIR = os.environ.get(
    "DATA_STUDY_GROUPS_DIR",
    os.path.join(DATA_DIR, "study_groups")
)

CONFIG_FILE = os.environ.get(
    "DATA_STUDY_GROUP_CONF",
    "study_groups.conf"
)

COMMON_REPORTS_DIR = os.environ.get(
    "DATA_STUDY_GROUPS_COMMON_REPORTS_DIR",
    os.path.join(DATA_DIR, "commonReports")
)
