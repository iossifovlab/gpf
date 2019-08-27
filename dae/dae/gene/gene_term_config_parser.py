from dae.configuration.dae_config_parser import DAEConfigParser


class GeneTermConfigParser(DAEConfigParser):

    @staticmethod
    def _get_gene_term(gene_terms):
        for gene_term_id, gene_term in gene_terms.items():
            if not isinstance(gene_term, dict):
                continue

            gene_term['id'] = gene_term_id

        return gene_terms

    @classmethod
    def parse(cls, config):
        config = super(GeneTermConfigParser, cls).parse_section(config)
        if config is None:
            return None

        gene_term_config = cls._get_gene_term(config.get('geneTerms', {}))

        return gene_term_config
