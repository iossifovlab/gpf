from __future__ import unicode_literals
from builtins import object
from Config import Config
from future import standard_library
standard_library.install_aliases()
from configparser import ConfigParser
from box import Box

import common.config
from variants.attributes import Role


class CommonReportsConfig(object):
    """
    Helper class for accessing DAE and commonReports configuration.
    """

    def __init__(self, config=None):
        if config is None:
            config = Config()
        self.dae_config = config

        wd = self.dae_config.daeDir
        data_dir = self.dae_config.data_dir

        config = ConfigParser({
            'wd': wd,
            'data': data_dir
        })
        config.read(self.dae_config.commonReportsConfFile)

        self.config = Box(common.config.to_dict(config))

    def _parse_data(self, data):
        parsed_data = {}
        for d in data.split(','):
            split_data = d.split(':')
            if len(split_data) == 1:
                continue
            parsed_data[split_data[0]] = split_data[1]
        return parsed_data

    def _parse_domain_info(self, domain):
        id, name, color = domain.split(':')

        return {
            'id': id.strip(),
            'name': name.strip(),
            'color': color.strip()
        }

    def _parse_phenotype_domain(self, phenotype_domain):
        phenotype = {}

        for domain in phenotype_domain.split(','):
            domain_info = self._parse_domain_info(domain)
            phenotype[domain_info['id']] = domain_info

        return phenotype

    def _study_groups(self):
        return self._parse_data(
            self.config.CommonReports.get('study_groups', ''))

    def _studies(self):
        return self._parse_data(self.config.CommonReports.get('studies', ''))

    def _counters_roles(self):
        return [Role.from_name(role)
                for role in self.config.CommonReports.counters_role.split(',')]

    def _effect_groups(self):
        return self.config.CommonReports.effect_groups.split(',')

    def _effect_types(self):
        return self.config.CommonReports.effect_types.split(',')

    def _phenotype(self, phenotype):
        phenotype = self.config.CommonReports.get(phenotype)

        return {
            'name': phenotype.name,
            'domain': self._parse_phenotype_domain(phenotype.domain),
            'unaffected': self._parse_domain_info(phenotype.unaffected),
            'default': self._parse_domain_info(phenotype.default),
            'source': phenotype.source
        }

    def _phenotypes(self):
        phenotypes = self.config.CommonReports.phenotypes.split(',')
        phenotypes_info = {}
        for phenotype in phenotypes:
            phenotypes_info[phenotype] = self._phenotype(phenotype)

        return phenotypes_info
