from configuration.dae_config_parser import DAEConfigParser


class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)


class GeneTermConfigParser(DAEConfigParser):

    @classproperty
    def PARSE_TO_DICT(cls):
        return {
            'geneTerms': {
                'group': 'geneTerms',
                'getter': cls._get_gene_term,
                'default': []
            }
        }

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
    def parse(cls, config):
        config = super(GeneTermConfigParser, cls).parse(config)
        if config is None:
            return None

        gene_term_config = {
            gt['id']: gt for gt in config['geneTerms']
        }

        return gene_term_config
