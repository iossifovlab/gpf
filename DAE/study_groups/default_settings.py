import os
from datasets.default_settings import get_config as datasets_get_config


def get_config():
    result = {
        "DATA_DIR": os.environ.get(
            "DATA_STUDY_GROUPS_DIR",
            os.path.join(datasets_get_config().get('DATA_DIR'), "study_groups")
        ),
        "CONFIG_FILE": os.environ.get(
            "DATA_STUDY_GROUPS_CONF",
            "study_groups.conf"
        )
    }
    result["COMMON_REPORTS_DIR"] = os.environ.get(
        "DATA_STUDY_GROUPS_COMMON_REPORTS_DIR",
        os.path.join(result.get("DATA_DIR"), "commonReports"))
    result["DENOVO_GENE_SETS_DIR"] = os.environ.get(
        "DATA_STUDY_GROUPS_DENOVO_GENE_SETS_DIR",
        os.path.join(result.get("DATA_DIR"), "gene_sets"))

    return result
