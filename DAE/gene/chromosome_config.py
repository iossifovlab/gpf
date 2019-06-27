from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()  # noqa

from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig


class ChromosomeConfig(ConfigurableEntityConfig):

    def __init__(self, config=None, *args, **kwargs):
        super(ChromosomeConfig, self).__init__(config, *args, **kwargs)

    @classmethod
    def from_config(cls, config=None):
        if config is None:
            return None

        return ChromosomeConfig(config)
