from __future__ import unicode_literals, print_function, absolute_import
from future import standard_library
standard_library.install_aliases()  # noqa

from builtins import object
from Config import Config
from configparser import ConfigParser
from box import Box
from collections import OrderedDict

import common.config
from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig


class CommonReportsConfig(object):
    """
    Helper class for accessing DAE and commonReports configuration.
    """

    def __init__(self, config=None):
        if config is None:
            config = Config()
        self.dae_config = config

        config = ConfigParser()
        with open(self.dae_config.commonReportsConfFile, 'r') as f:
            config.read_file(f)

        self.config = Box(common.config.to_dict(config))

    def _parse_data(self, data):
        parsed_data = OrderedDict()
        for d in data.split(','):
            d_properties = self.config.CommonReports.get(d.lower())
            if d_properties is None:
                continue
            phenotypes = d_properties.get('peoplegroups', None)
            groups = d_properties.get('groups', None)
            draw_all_families = d_properties.get('draw_all_families', 'false')
            count_of_families_for_show_id =\
                d_properties.get('count_of_families_for_show_id', None)
            is_downloadable = d_properties.get('is_downloadable', 'false')

            if phenotypes is None or groups is None:
                continue
            if count_of_families_for_show_id is not None:
                count_of_families_for_show_id =\
                    int(count_of_families_for_show_id)
            draw_all_families =\
                ConfigurableEntityConfig._str_to_bool(draw_all_families)
            is_downloadable =\
                ConfigurableEntityConfig._str_to_bool(is_downloadable)

            parsed_data[d] = OrderedDict([
                ('phenotype_groups', phenotypes.split(',')),
                ('groups', OrderedDict([
                    (group.split(':')[1].strip(),
                     group.split(':')[0].strip().split(','))
                    for group in groups.split('|')])),
                ('draw_all_families', draw_all_families),
                ('families_count_show_id', count_of_families_for_show_id),
                ('is_downloadable', is_downloadable),
            ])
        return parsed_data

    def _parse_domain_info(self, domain):
        id, name, color = domain.split(':')

        return OrderedDict([
            ('id', id.strip()),
            ('name', name.strip()),
            ('color', color.strip())
        ])

    def _parse_phenotype_domain(self, phenotype_domain):
        phenotype = OrderedDict()

        for domain in phenotype_domain.split(','):
            domain_info = self._parse_domain_info(domain)
            phenotype[domain_info['id']] = domain_info

        return phenotype

    def study_groups(self):
        return self._parse_data(
            self.config.CommonReports.get('study_groups', ''))

    def studies(self):
        return self._parse_data(self.config.CommonReports.get('studies', ''))

    def effect_groups(self):
        effect_groups = self.config.CommonReports.get('effect_groups', None)
        return effect_groups.split(',') if effect_groups else []

    def effect_types(self):
        effect_types = self.config.CommonReports.get('effect_types', None)
        return effect_types.split(',') if effect_types else []

    def _phenotype(self, phenotype):
        phenotype = self.config.CommonReports.get(phenotype)

        return OrderedDict([
            ('name', phenotype.get('name')),
            ('domain', self._parse_phenotype_domain(phenotype.get('domain'))),
            ('unaffected',
             self._parse_domain_info(phenotype.get('unaffected'))),
            ('default', self._parse_domain_info(phenotype.get('default'))),
            ('source', phenotype.get('source'))
        ])

    def phenotypes(self):
        phenotypes = self.config.CommonReports.peoplegroups.split(',')
        phenotypes_info = OrderedDict()
        for phenotype in phenotypes:
            phenotypes_info[phenotype] = self._phenotype(phenotype)

        return phenotypes_info
