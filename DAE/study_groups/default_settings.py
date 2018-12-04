import os
from studies.default_settings import get_config as studies_get_config


def get_config():
    result = {
        "CONFIG_FILE": os.environ.get(
            "DATA_STUDIES_CONF",
            "study_groups.conf"
        ),
        "DATA_DIR": studies_get_config().get("DATA_DIR")
    }
    result["COMMON_REPORTS_DIR"] = os.environ.get(
        "DATA_STUDY_GROUPS_COMMON_REPORTS_DIR",
        os.path.join(result.get("DATA_DIR"), "commonReports"))

    return result
