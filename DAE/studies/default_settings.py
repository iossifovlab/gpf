import os
from datasets.default_settings import get_config as datasets_get_config


def get_config():
    return {
        "DATA_DIR": os.environ.get(
            "DATA_STUDIES_DIR",
            os.path.join(datasets_get_config().get('DATA_DIR'), "studies")
        ),
        "CONFIG_FILE": os.environ.get("DATA_STUDIES_CONF", "studies.conf")
    }
