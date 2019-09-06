from dae.configuration.config_parser_base import ConfigParserBase

from dae.RegionOperations import Region


class GenomesDBConfigParser(ConfigParserBase):

    @classmethod
    def _get_regions(cls, regions):
        for region_id in regions.keys():
            region = regions[region_id]

            reg = cls._split_str_option_list(region)
            regions[region_id] = {'region': [Region.from_str(r) for r in reg]}

        return regions

    @classmethod
    def parse(cls, config):
        config = super(GenomesDBConfigParser, cls).parse(config)

        config.PARs.regions = cls._get_regions(config.PARs.regions)

        return config
