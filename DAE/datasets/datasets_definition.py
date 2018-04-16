import os

from datasets.dataset import Dataset
from datasets.dataset_config import DatasetConfig
from datasets.dataset_factory import DatasetFactory


class DatasetsDefinition(object):

    ENABLED_DIR = 'datasets-enabled'

    def __init__(self, datasets_dir=None):
        if datasets_dir is None:
            from default_settings import DATA_DATASETS_DIR
            datasets_dir = DATA_DATASETS_DIR

        assert isinstance(datasets_dir, str), type(datasets_dir)
        assert os.path.exists(datasets_dir), datasets_dir

        self.datasets_dir = datasets_dir

        enabled_dir = os.path.join(datasets_dir, DatasetsDefinition.ENABLED_DIR)
        assert os.path.exists(enabled_dir), enabled_dir
        assert os.path.isdir(enabled_dir), enabled_dir

        config_paths = []
        configs = []

        for path in os.listdir(enabled_dir):
            if os.path.isdir(path) and path.endswith('.conf'):
                config_paths.append(path)

        print(config_paths)

        for config_path in config_paths:
            configs.append(DatasetConfig.from_config(config_path))

        self.configs = {conf.dataset_name: conf for conf in configs}

    @property
    def enabled_dataset_ids(self):
        return list(self.configs.keys())

    def get_dataset_config(self, dataset_id):
        if dataset_id not in self.configs:
            return None

        return self.configs[dataset_id]
