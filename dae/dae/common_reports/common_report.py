import time
from collections import OrderedDict

from dae.variants.attributes import Role
from dae.pedigrees.families_groups import FamiliesGroups

from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.denovo_report import DenovoReport
# from dae.common_reports.people_group_info import PeopleGroupsInfo
from dae.common_reports.people_filters import FilterCollection


class CommonReport(object):

    def __init__(self, genotype_data_study, config):
        people_groups = config.people_group
        effect_groups = config.effect_groups
        effect_types = config.effect_types

        self.genotype_data_study = genotype_data_study
        self.families_groups = FamiliesGroups.from_config(
            genotype_data_study.families,
            people_groups
        )
        self.families_groups.add_predefined_groups(
            ['status', 'sex', 'role', 'role.sex', 'family_size'])

        people_filters = FilterCollection.build_filter_objects(
            self.families_groups, config.groups
        )
        denovo_people_filters = [
            pf for pf in people_filters
            if pf.group_id in config.selected_people_groups
        ]

        self.id = genotype_data_study.id

        start = time.time()
        self.families_report = FamiliesReport(
            config.selected_people_groups, self.families_groups,
            people_filters,
            config.draw_all_families, config.families_count_show_id
        )
        elapsed = time.time() - start
        print(
            f"COMMON REPORTS family report "
            f"build in {elapsed:.2f} sec")

        start = time.time()
        self.denovo_report = DenovoReport(
            genotype_data_study, effect_groups, effect_types,
            denovo_people_filters)
        elapsed = time.time() - start
        print(
            f"COMMON REPORTS denovo report "
            f"build in {elapsed:.2f} sec")

        self.study_name = genotype_data_study.name
        self.phenotype = self._get_phenotype()
        self.study_type = ','.join(genotype_data_study.study_type)\
            if genotype_data_study.study_type else None
        self.study_year = genotype_data_study.year
        self.pub_med = genotype_data_study.pub_med

        self.families = len(genotype_data_study.families.values())
        self.number_of_probands =\
            self._get_number_of_people_with_role(Role.prb)
        self.number_of_siblings =\
            self._get_number_of_people_with_role(Role.sib)
        self.denovo = genotype_data_study.has_denovo
        self.transmitted = genotype_data_study.has_transmitted
        self.study_description = genotype_data_study.description

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
        families_group = \
            self.families_groups.get_default_families_group()
        return families_group.available_values

    def _get_number_of_people_with_role(self, role):
        role_group = self.families_groups['role']
        return len(role_group.get_people_with_propvalues((role,)))
