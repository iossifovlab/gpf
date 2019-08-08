from configuration.dae_config_parser import DAEConfigParser


class GeneWeightConfigParser(DAEConfigParser):

    SECTION = 'geneWeights'

    SPLIT_STR_LISTS = (
        'weights',
        'range',
    )

    CAST_TO_INT = (
        'bins',
    )

    @classmethod
    def parse(cls, config):
        config = super(GeneWeightConfigParser, cls).parse(config)
        if config is None:
            return None

        weight_config = config.get(cls.SECTION, None)

        for weight in weight_config.weights:
            weight_config[weight] = super(GeneWeightConfigParser, cls).parse(
                config.get('geneWeights.{}'.format(weight)))
            weight_config[weight]['name'] = weight

        return weight_config
