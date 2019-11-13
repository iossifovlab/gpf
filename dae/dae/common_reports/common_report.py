from collections import OrderedDict

from dae.variants.attributes import Role

from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.denovo_report import DenovoReport
from dae.common_reports.people_group_info import PeopleGroupsInfo
from dae.common_reports.filter import FilterObjects


class CommonReport(object):

    def __init__(self, study, config):
        people_groups_info = config.people_groups_info
        effect_groups = config.effect_groups
        effect_types = config.effect_types

        self.study = study
        self.people_groups_info = PeopleGroupsInfo(
            study, config.people_groups, people_groups_info
        )

        filter_objects = FilterObjects.get_filter_objects(
            study, self.people_groups_info, config.groups
        )

        self.id = study.id
        self.families_report = FamiliesReport(
            study, self.people_groups_info, filter_objects,
            config.draw_all_families, config.families_count_show_id
        )
        self.denovo_report = DenovoReport(
            study, effect_groups, effect_types, filter_objects)
        self.study_name = study.name
        self.phenotype = self._get_phenotype()
        self.study_type = ','.join(study.study_types)\
            if study.study_types else None
        self.study_year = study.year
        self.pub_med = study.pub_med

        self.families = len(study.families.values())
        self.number_of_probands =\
            self._get_number_of_people_with_role(Role.prb)
        self.number_of_siblings =\
            self._get_number_of_people_with_role(Role.sib)
        self.denovo = study.has_denovo
        self.transmitted = study.has_transmitted
        self.study_description = study.description

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

    def _get_phenotype(self):
        people_group_info = \
            self.people_groups_info.get_first_people_group_info()
        default_phenotype = people_group_info.default['name']

        return [pheno if pheno is not None else default_phenotype
                for pheno in people_group_info.people_groups]

    def _get_number_of_people_with_role(self, role):
        return sum([len(family.get_people_with_role(role))
                    for family in self.study.families.values()])
