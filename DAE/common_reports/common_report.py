from __future__ import unicode_literals
from __future__ import division

import os
import json
from collections import OrderedDict

from variants.attributes import Role

from common_reports.family_report import FamiliesReport
from common_reports.denovo_report import DenovoReport
from common_reports.phenotype_info import PhenotypesInfo
from common_reports.filter import FilterObjects


class CommonReport(object):

    def __init__(
            self, query_object, filter_info, phenotypes_info, effect_groups,
            effect_types):
        phenotypes_info = PhenotypesInfo(
            query_object, filter_info, phenotypes_info)

        filter_objects = FilterObjects.get_filter_objects(
            query_object, phenotypes_info, filter_info['groups'])

        self.id = filter_info['id']
        self.families_report = FamiliesReport(
            query_object, phenotypes_info, filter_objects,
            filter_info['draw_all_families'],
            filter_info['families_count_show_id'])
        self.denovo_report = DenovoReport(
            query_object, effect_groups, effect_types, filter_objects)
        self.study_name = query_object.name
        self.phenotype = self._get_phenotype(phenotypes_info)
        self.study_type = ','.join(query_object.study_types)\
            if query_object.study_types else None
        self.study_year = query_object.year
        self.pub_med = query_object.pub_med

        self.families = len(query_object.families)
        self.number_of_probands =\
            self._get_number_of_people_with_role(query_object, Role.prb)
        self.number_of_siblings =\
            self._get_number_of_people_with_role(query_object, Role.sib)
        self.denovo = query_object.has_denovo
        self.transmitted = query_object.has_transmitted
        self.study_description = query_object.description

    def to_dict(self):
        return OrderedDict([
            ('id', self.id),
            ('families_report', self.families_report.to_dict()),
            ('denovo_report', (
                self.denovo_report.to_dict()
                if not self.denovo_report.is_empty() else None
            )),
            ('study_name', self.study_name),
            ('phenotype', self.phenotype),
            ('study_type', self.study_type),
            ('study_year', self.study_year),
            ('pub_med', self.pub_med),
            ('families', self.families),
            ('number_of_probands', self.number_of_probands),
            ('number_of_siblings', self.number_of_siblings),
            ('denovo', self.denovo),
            ('transmitted', self.transmitted),
            ('study_description', self.study_description)
        ])

    def _get_phenotype(self, phenotypes_info):
        phenotype_info = phenotypes_info.get_first_phenotype_info()
        default_phenotype = phenotype_info.default['name']

        return [pheno if pheno is not None else default_phenotype
                for pheno in phenotype_info.phenotypes]

    def _get_number_of_people_with_role(self, query_object, role):
        return sum([len(family.get_people_with_role(role))
                    for family in query_object.families.values()])


class CommonReportsGenerator(object):

    def __init__(self, common_reports_query_objects):
        assert common_reports_query_objects is not None

        self.query_objects_with_config =\
            common_reports_query_objects.query_objects_with_config

    def save_common_reports(self):
        for query_object, config in self.query_objects_with_config.items():
            if config is None:
                continue

            phenotypes_info = config.phenotypes_info
            filter_info = config.filter_info
            effect_groups = config.effect_groups
            effect_types = config.effect_types

            path = config.path

            common_report = CommonReport(
                query_object, filter_info, phenotypes_info, effect_groups,
                effect_types)

            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            with open(path, 'w+') as crf:
                json.dump(common_report.to_dict(), crf)
