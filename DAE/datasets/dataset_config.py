import os
import reusables
from box import ConfigBox


class DatasetConfig(ConfigBox):

    def __init__(self, *args, **kwargs):
        super(DatasetConfig, self).__init__(*args, **kwargs)
        assert self.dataset_name
        assert self.variants

    @staticmethod
    def from_config(path):
        assert os.path.exists(path)

        config = reusables.config_dict(
            path,
            auto_find=False,
            verify=True,
        )

        return DatasetConfig(config)
