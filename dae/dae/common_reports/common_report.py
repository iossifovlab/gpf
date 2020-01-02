from collections import OrderedDict

from dae.variants.attributes import Role
from dae.pedigrees.families_groups import FamiliesGroups

from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.denovo_report import DenovoReport
# from dae.common_reports.people_group_info import PeopleGroupsInfo
from dae.common_reports.people_filters import FilterCollection


class CommonReport(object):

    def __init__(self, genotype_data_study, config):
        people_groups_info = config.people_groups_info
        effect_groups = config.effect_groups
        effect_types = config.effect_types

        self.genotype_data_study = genotype_data_study
        self.families_groups = FamiliesGroups.from_config(
            genotype_data_study.families,
            config.people_groups,
            people_groups_info
        )
        self.families_groups.add_predefined_groups(['status', 'sex', 'role'])

        filter_objects = FilterCollection.build_filter_objects(
            self.families_groups, config.groups
        )

        self.id = genotype_data_study.id
        self.families_report = FamiliesReport(
            genotype_data_study, self.families_groups, filter_objects,
            config.draw_all_families, config.families_count_show_id
        )
        self.denovo_report = DenovoReport(
            genotype_data_study, effect_groups, effect_types, filter_objects)
        self.study_name = genotype_data_study.name
        self.phenotype = self._get_phenotype()
        self.study_type = ','.join(genotype_data_study.study_types)\
            if genotype_data_study.study_types else None
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
        default_phenotype = families_group.default.name

        return [pheno if pheno is not None else default_phenotype
                for pheno in families_group.available_values]

    def _get_number_of_people_with_role(self, role):
        return len(self.genotype_data_study.families.persons_with_roles(
            [role]))
