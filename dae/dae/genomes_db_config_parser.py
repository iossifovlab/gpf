from dae.configuration.config_parser_base import ConfigParserBase

from dae.RegionOperations import Region


class GenomesDBConfigParser(ConfigParserBase):

    @classmethod
    def _get_regions(cls, regions):
        new_regions = {}
        for region_id, region in regions.items():
            new_region = {}

            reg = cls._split_str_option_list(region)
            new_region['region'] = [Region.from_str(r) for r in reg]

            new_regions[region_id] = new_region

        return new_regions

    @classmethod
    def parse(cls, config):
        config = super(GenomesDBConfigParser, cls).parse(config)

        config['PARs']['regions'] = cls._get_regions(config['PARs']['regions'])

        return config
