from __future__ import unicode_literals, print_function, absolute_import
from future import standard_library
standard_library.install_aliases()  # noqa

from builtins import object
import os
from box import Box
from collections import OrderedDict

from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig
from configurable_entities.configurable_entity_definition import\
    ConfigurableEntityDefinition


class CommonReportsConfig(ConfigurableEntityConfig):
    """
    Helper class for accessing DAE and commonReports configuration.
    """

    SPLIT_STR_LISTS = ('peopleGroups', 'effect_groups', 'effect_types')
    CAST_TO_BOOL = ('draw_all_families', 'is_downloadable', 'enabled')

    def __init__(
            self, id, config, phenotypes_info, filter, query_object, path,
            *args, **kwargs):
        super(CommonReportsConfig, self).__init__(config, *args, **kwargs)

        self.id = id

        self.phenotypes_info = phenotypes_info
        self.filter = filter
        self.effect_groups =\
            self.config.commonReport.get('effect_groups', [])
        self.effect_types = self.config.commonReport.get('effect_types', [])

        self.query_object = query_object

        self.path = path

    @staticmethod
    def _parse_domain_info(domain):
        id, name, color = domain.split(':')

        return OrderedDict([
            ('id', id.strip()),
            ('name', name.strip()),
            ('color', color.strip())
        ])

    @classmethod
    def _parse_phenotype_domain(cls, phenotype_domain):
        phenotype = OrderedDict()

        for domain in phenotype_domain.split(','):
            domain_info = cls._parse_domain_info(domain)
            phenotype[domain_info['id']] = domain_info

        return phenotype

    @classmethod
    def _parse_phenotype(cls, config, phenotype):
        return OrderedDict([
            ('name', config.commonReport.get(phenotype + '.name')),
            ('domain', cls._parse_phenotype_domain(
                config.commonReport.get(phenotype + '.domain'))),
            ('unaffected', cls._parse_domain_info(
                config.commonReport.get(phenotype + '.unaffected'))),
            ('default', cls._parse_domain_info(
                config.commonReport.get(phenotype + '.default'))),
            ('source', config.commonReport.get(phenotype + '.source'))
        ])

    @classmethod
    def _parse_phenotypes(cls, config):
        phenotypes = config.commonReport.peopleGroups
        phenotypes_info = OrderedDict()
        for phenotype in phenotypes:
            pheno = 'peopleGroup.' + phenotype
            phenotypes_info[phenotype] =\
                cls._parse_phenotype(config, pheno)

        return phenotypes_info

    @staticmethod
    def _parse_data(config):
        phenotypes = config.commonReport.get('peopleGroups', None)
        groups = config.commonReport.get('groups', None)
        draw_all_families =\
            config.commonReport.get('draw_all_families', False)
        count_of_families_for_show_id =\
            config.commonReport.get('count_of_families_for_show_id', None)
        is_downloadable = config.commonReport.get('is_downloadable', False)

        if phenotypes is None or groups is None:
            return None
        if count_of_families_for_show_id is not None:
            count_of_families_for_show_id =\
                int(count_of_families_for_show_id)

        return OrderedDict([
            ('phenotype_groups', phenotypes),
            ('groups', OrderedDict([
                (group.split(':')[1].strip(),
                    group.split(':')[0].strip().split(','))
                for group in groups.split('|')])),
            ('draw_all_families', draw_all_families),
            ('families_count_show_id', count_of_families_for_show_id),
            ('is_downloadable', is_downloadable),
        ])

    @classmethod
    def from_config(cls, config_file, facade):
        config = Box(cls.get_config(config_file, ''))

        if 'commonReport' not in config or\
                config.commonReport.get('enabled', True) is False:
            return None

        id = ''
        for key in config.keys():
            if 'id' in config[key]:
                id = config[key].id

        try:
            query_object = facade.get_study_wrapper(id)
        except (KeyError, AttributeError):
            query_object = facade.get_dataset_wrapper(id)

        phenotypes_info = cls._parse_phenotypes(config)
        filter = cls._parse_data(config)
        if filter is None:
            return None

        path = os.path.join(
            os.path.split(config_file)[0], 'commonReport/' + id + '.json')

        return CommonReportsConfig(
            id, config, phenotypes_info, filter, query_object, path)


class CommonReportsConfigs(object):

    def __init__(self):
        self.common_reports_configs = []

    def scan_directory(self, directory, facade):
        config_files =\
            ConfigurableEntityDefinition._collect_config_paths(directory)

        for config_file in config_files:
            config = CommonReportsConfig.from_config(config_file, facade)

            if config:
                self.common_reports_configs.append(config)
