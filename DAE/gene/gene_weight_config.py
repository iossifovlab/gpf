from configuration.config_base import ConfigBase


class GeneWeightConfig(ConfigBase):
    SPLIT_STR_LISTS = (
        'weights',
        'range',
    )

    CAST_TO_INT = (
        'bins',
    )

    def __init__(self, config, *args, **kwargs):
        super(GeneWeightConfig, self).__init__(config, *args, **kwargs)

    @classmethod
    def from_config(cls, config):
        if config is None:
            return None

        weight_config = config.get('geneWeights', None)
        weight_config = cls.parse(weight_config)

        for weight in weight_config.weights:
            weight_config[weight] = cls.parse(
                config.get('geneWeights.{}'.format(weight)))

        return GeneWeightConfig(weight_config)
