from dae.configuration.config_parser_base import ConfigParserBase


class GeneWeightConfigParser(ConfigParserBase):

    SPLIT_STR_LISTS = (
        'weights',
        'range',
    )

    CAST_TO_INT = (
        'bins',
    )

    FILTER_SELECTORS = {
        'geneWeights': 'selected_gene_weights_values',
    }

    @classmethod
    def _parse_gene_weights(cls, gene_weights):
        gene_weights = super(GeneWeightConfigParser, cls).parse(gene_weights)
        if not gene_weights:
            gene_weights = {}

        for gene_weight in gene_weights.values():
            if gene_weight.range:
                gene_weight.range = tuple(map(float, gene_weight.range))

        return gene_weights

    @classmethod
    def parse(cls, config):
        config = super(GeneWeightConfigParser, cls).parse(config)
        if config is None:
            return None

        selected_gene_weights_values = config.gene_weights.weights
        config.selected_gene_weights_values = selected_gene_weights_values
        config = super(GeneWeightConfigParser, cls).parse_section(config)

        weight_config = cls._parse_gene_weights(config.gene_weights)

        return weight_config
