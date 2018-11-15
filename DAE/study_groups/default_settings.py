import os
from studies.default_settings import get_config as studies_get_config


def get_config():
    return {
        "CONFIG_FILE": os.environ.get(
            "DATA_STUDIES_CONF",
            "study_groups.conf"
        ),
        "DATA_DIR": studies_get_config().get("DATA_DIR")
    }
