from dae.configuration.dae_config_parser import DAEConfigParser


class GeneWeightConfigParser(DAEConfigParser):

    SPLIT_STR_LISTS = (
        'weights',
        'range',
    )

    CAST_TO_INT = (
        'bins',
    )

    @classmethod
    def _get_gene_weights(cls, gene_weights):
        for gene_weight_id, gene_weight in gene_weights.items():
            if not isinstance(gene_weight, dict):
                continue

            gene_weight['id'] = gene_weight_id
            gene_weight['name'] = gene_weight_id

        gene_weights = super(GeneWeightConfigParser, cls).parse(gene_weights)

        return gene_weights

    @classmethod
    def parse(cls, config):
        config = super(GeneWeightConfigParser, cls).parse(config)
        if config is None:
            return None

        config['geneWeights'] = \
            cls._get_gene_weights(config.get('geneWeights', {}))

        weight_config = config.get('geneWeights', {})

        return weight_config
