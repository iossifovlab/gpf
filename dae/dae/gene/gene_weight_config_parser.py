from dae.configuration.dae_config_parser import DAEConfigParser


class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)


class GeneWeightConfigParser(DAEConfigParser):

    SPLIT_STR_LISTS = (
        'weights',
        'range',
    )

    CAST_TO_INT = (
        'bins',
    )

    @classproperty
    def PARSE_TO_LIST(cls):
        return {
            'geneWeights': {
                'group': 'geneWeights',
                'getter': cls._get_gene_weights,
                'default': []
            }
        }

    CONVERT_LIST_TO_DICT = ['geneWeights']

    @staticmethod
    def _get_gene_weights(gene_weights_type, gene_weights_options, config):
        for gwo in gene_weights_options:
            gwt = gene_weights_type
            if gwo is not None:
                gwt = '.'.join([gwt, gwo])

            gene_weights = config.pop(gwt)
            gene_weights['id'] = gwt.split('.', 1)[-1]
            gene_weights['name'] = gene_weights['id']

            yield gene_weights

    @classmethod
    def parse(cls, config):
        config = super(GeneWeightConfigParser, cls).parse(config)
        config = super(GeneWeightConfigParser, cls).parse_section(config)
        if config is None:
            return None

        weight_config = config.get('geneWeights', None)
        weight_config['weights'] = list(weight_config.keys())

        return weight_config
