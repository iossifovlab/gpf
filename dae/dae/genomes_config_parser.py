from dae.configuration.dae_config_parser import DAEConfigParser

from dae.RegionOperations import Region


class GenomesConfigParser(DAEConfigParser):

    @classmethod
    def _get_regions(cls, regions):
        new_regions = {}
        for region_id, region in regions.items():
            new_region = {}
            new_region['id'] = region_id

            reg = cls._split_str_option_list(region)
            new_region['region'] = [Region.from_str(r) for r in reg]

            new_regions[region_id] = new_region

        return new_regions

    @staticmethod
    def _get_genomes(genomes):
        for genome_id, genome in genomes.items():
            genome['id'] = genome_id
            for gene_model_id, gene_model in \
                    genome.get('geneModel', {}).items():
                gene_model['id'] = gene_model_id

        return genomes

    @classmethod
    def parse(cls, config):
        config = super(GenomesConfigParser, cls).parse(config)

        config['genome'] = cls._get_genomes(config.get('genome', {}))
        config['mito_genome'] = cls._get_genomes(config.get('mito_genome', {}))
        config['PARs']['regions'] = cls._get_regions(config['PARs']['regions'])

        return config
