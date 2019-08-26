from dae.configuration.dae_config_parser import DAEConfigParser

from dae.RegionOperations import Region


class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)


class GenomesConfigParser(DAEConfigParser):

    @classproperty
    def PARSE_TO_LIST(cls):
        return {
            'regions': {
                'group': 'regions',
                'getter': cls._get_regions,
            }, 'genome': {
                'group': 'genome',
                'getter': cls._get_genome,
            }, 'mito_genome': {
                'group': 'mito_genome',
                'getter': cls._get_genome,
            }, 'geneModel': {
                'group': 'geneModel',
                'getter': cls._get_gene_model,
            }
        }

    CONVERT_LIST_TO_DICT = (
        'regions',
        'genome',
        'mito_genome',
        'geneModel',
    )

    @classmethod
    def _get_regions(cls, regions_type, regions_options, genomes_db_config):
        regions = {}

        regions['id'] = regions_type.split('.')[-1]

        region = cls._split_str_option_list(
            genomes_db_config.get(regions_type, ''))

        regions['region'] = [Region.from_str(reg) for reg in region]

        yield regions

    @staticmethod
    def _get_genome(genome_type, genome_options, genomes_db_config):
        genome = genomes_db_config.get(genome_type, dict())
        genome['id'] = genome_type.split('.')[-1]

        yield genome

    @staticmethod
    def _get_gene_model(
            gene_model_type, gene_model_options, genomes_db_config):
        for gmo in gene_model_options:
            gene_model = {}

            gene_model['id'] = gene_model_type.split('.')[-1]
            gene_model['file'] = genomes_db_config.get(
                f'{gene_model_type}.{gmo}', dict())

            yield gene_model

    @classmethod
    def parse(cls, config):
        config = super(GenomesConfigParser, cls).parse(config)
        config = super(GenomesConfigParser, cls).parse_section(config)

        return config
