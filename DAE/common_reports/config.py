from __future__ import unicode_literals, print_function, absolute_import
from future import standard_library; standard_library.install_aliases()  # noqa

from builtins import object
import os

from box import Box
from collections import OrderedDict
from copy import deepcopy

from configurable_entities.configurable_entity_config import\
    ConfigurableEntityConfig


class CommonReportsConfig(object):
    """
    Helper class for accessing DAE and commonReports configuration.
    """

    def __init__(
            self, id, config, people_groups_info, filter_info):
        self.config = config

        self.id = id

        self.people_groups_info = people_groups_info
        self.filter_info = filter_info
        self.effect_groups = self.config.get('effect_groups', [])
        self.effect_types = self.config.get('effect_types', [])

        self.path = config.file


class CommonReportsParseConfig(ConfigurableEntityConfig):

    SPLIT_STR_LISTS = ('peopleGroups', 'effect_groups', 'effect_types')
    CAST_TO_BOOL = ('draw_all_families', 'enabled')

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
        people_groups_info = OrderedDict()
        for phenotype in phenotypes:
            pheno = 'peopleGroup.' + phenotype
            people_groups_info[phenotype] =\
                cls._parse_phenotype(config, pheno)

        return people_groups_info

    @staticmethod
    def _parse_data(config, id):
        phenotypes = config.get('peopleGroups', None)
        groups = config.get('groups', None)
        draw_all_families =\
            config.get('draw_all_families', False)
        count_of_families_for_show_id =\
            config.get('count_of_families_for_show_id', None)

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
            ('id', id),
        ])

    @classmethod
    def from_config(cls, study_config):
        id = study_config.id
        config = deepcopy(
            study_config.study_config.get('commonReport', None))
        config_file = study_config.study_config.get('config_file', '')

        if config is None:
            return None

        config = cls.parse(config)
        config = Box(config)

        if config.get('enabled', True) is False:
            return None

        people_groups_info = cls._parse_phenotypes(config)
        filter_info = cls._parse_data(config, id)
        if filter_info is None:
            return None

        assert os.path.exists(config_file)

        if config.get('file') is None:
            dirname = os.path.dirname(config_file)
            filename = os.path.join(dirname, 'common_report.json')
            config.file = filename

        return CommonReportsConfig(
            id, config, people_groups_info, filter_info)


class CommonReportsStudies(object):

    def __init__(self, study_facade, dataset_facade):
        studies = study_facade.get_all_studies_wrapper() +\
            dataset_facade.get_all_datasets_wrapper()
        self.studies_with_config = {}
        for study in studies:
            common_report_config = \
                CommonReportsParseConfig.from_config(study.config)
            if common_report_config is not None:
                self.studies_with_config[study] = common_report_config

    def filter_studies(self, studies):
        self.studies_with_config = {
            qo: c
            for qo, c in self.studies_with_config.items()
            if qo.id in studies
        }
