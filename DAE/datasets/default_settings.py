import os


def get_config():
    data_dir = os.environ.get("DAE_DB_DIR", ".")
    return {
        "DATA_DIR": data_dir,
        "DATA_DATASETS_DIR": os.environ.get(
            "DATA_DATASETS_DIR", "{}/datasets".format(data_dir))
    }
