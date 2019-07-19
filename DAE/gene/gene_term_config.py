from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()  # noqa

from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig


class GeneTermConfig(ConfigurableEntityConfig):

    def __init__(self, config, *args, **kwargs):
        super(GeneTermConfig, self).__init__(config, *args, **kwargs)

    @staticmethod
    def _get_gene_term(gene_term_type, gene_term_options, config):
        for gto in gene_term_options:
            gtt = gene_term_type
            if gto is not None:
                gtt = '.'.join([gtt, gto])

            gene_term = config.pop(gtt).to_dict()
            gene_term['id'] = gtt.split('.', 1)[-1]

            yield gene_term

    @classmethod
    def from_config(cls, config):
        if config is None:
            return None

        gene_terms = cls._get_selectors(
            config, 'geneTerms', cls._get_gene_term)

        gene_term_config = {gt['id']: gt for gt in gene_terms}

        return GeneTermConfig(gene_term_config)
