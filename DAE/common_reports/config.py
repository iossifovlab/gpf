from __future__ import unicode_literals, print_function, absolute_import
from future import standard_library
standard_library.install_aliases()  # noqa

from builtins import object
import os
from box import Box
from collections import OrderedDict

from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig


class CommonReportsConfig(object):
    """
    Helper class for accessing DAE and commonReports configuration.
    """

    def __init__(
            self, id, config, phenotypes_info, filter_info, path):
        self.config = config

        self.id = id

        self.phenotypes_info = phenotypes_info
        self.filter_info = filter_info
        self.effect_groups = self.config.get('effect_groups', [])
        self.effect_types = self.config.get('effect_types', [])

        self.path = path


class CommonReportsParseConfig(ConfigurableEntityConfig):

    SPLIT_STR_LISTS = ('peopleGroups', 'effect_groups', 'effect_types')
    CAST_TO_BOOL = ('draw_all_families', 'is_downloadable', 'enabled')

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
            ('name', config.get(phenotype + '.name')),
            ('domain', cls._parse_phenotype_domain(
                config.get(phenotype + '.domain'))),
            ('unaffected', cls._parse_domain_info(
                config.get(phenotype + '.unaffected'))),
            ('default', cls._parse_domain_info(
                config.get(phenotype + '.default'))),
            ('source', config.get(phenotype + '.source'))
        ])

    @classmethod
    def _parse_phenotypes(cls, config):
        phenotypes = config.peopleGroups
        phenotypes_info = OrderedDict()
        for phenotype in phenotypes:
            pheno = 'peopleGroup.' + phenotype
            phenotypes_info[phenotype] =\
                cls._parse_phenotype(config, pheno)

        return phenotypes_info

    @staticmethod
    def _parse_data(config):
        phenotypes = config.get('peopleGroups', None)
        groups = config.get('groups', None)
        draw_all_families =\
            config.get('draw_all_families', False)
        count_of_families_for_show_id =\
            config.get('count_of_families_for_show_id', None)
        is_downloadable = config.get('is_downloadable', False)

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
    def from_config(cls, query_object_config):
        id = query_object_config.id
        config = query_object_config.study_config.get('commonReport', None)
        config_file = query_object_config.study_config.get('config_file', '')

        if config is None:
            return None

        config = cls.parse(config)
        config = Box(config)

        if config.get('enabled', True) is False:
            return None

        phenotypes_info = cls._parse_phenotypes(config)
        filter_info = cls._parse_data(config)
        if filter_info is None:
            return None

        assert os.path.exists(config_file)
        path = os.path.join(
            os.path.split(config_file)[0], 'commonReport/' + id + '.json')

        return CommonReportsConfig(
            id, config, phenotypes_info, filter_info, path)


class CommonReportsQueryObjects(object):

    def __init__(self, study_facade, dataset_facade):
        query_objects = study_facade.get_all_studies_wrapper() +\
            dataset_facade.get_all_datasets_wrapper()

        self.query_objects_with_config = {}

        for query_object in query_objects:
            common_report_config =\
                CommonReportsParseConfig.from_config(query_object.config)
            if common_report_config is not None:
                self.query_objects_with_config[query_object] =\
                    common_report_config
