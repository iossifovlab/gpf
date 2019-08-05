from configuration.config_base import\
    ConfigurableEntityConfig


class ChromosomeConfig(ConfigurableEntityConfig):

    def __init__(self, config=None, *args, **kwargs):
        super(ChromosomeConfig, self).__init__(config, *args, **kwargs)

    @classmethod
    def from_config(cls, config=None):
        if config is None:
            return None

        return ChromosomeConfig(config)
