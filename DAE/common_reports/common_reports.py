import pandas as pd
import json
import os

from config import CommonReportsConfig
from study_groups.study_group_facade import StudyGroupFacade
from studies.study_facade import StudyFacade
from variants.attributes import Role, Sex, Inheritance
from common.query_base import EffectTypesMixin
from studies.default_settings import COMMON_REPORTS_DIR\
    as studies_common_reports_dir
from study_groups.default_settings import COMMON_REPORTS_DIR\
    as study_groups_common_reports_dir


class CommonReportsGenerator(CommonReportsConfig):

    def __init__(self):
        super(CommonReportsGenerator, self).__init__()
        self.study_groups = self._study_groups()
        self.studies = self._studies()
        self.counters_roles = self._counters_roles()
        self.effect_groups = self._effect_groups()
        self.effect_types = self._effect_types()
        self.phenotypes = self._phenotypes()

        self.study_group_facade = StudyGroupFacade()
        self.study_facade = StudyFacade()

        self.effect_types_converter = EffectTypesMixin()

    def get_people(
            self, sex, phenotype, phenotype_column, families, counter_roles):
        people = []
        for family in families.values():
            people_with_role =\
                family.get_people_with_roles(counter_roles)
            people += list(filter(
                lambda pwr: pwr.sex == sex and
                pwr.get_attr(phenotype_column) == phenotype,
                people_with_role))
        return people

    def get_people_counters(
            self, phenotype, phenotype_column, families, counter_roles):
        people_male = len(self.get_people(
            Sex.male, phenotype, phenotype_column, families, counter_roles))
        people_female = len(self.get_people(
            Sex.female, phenotype, phenotype_column, families, counter_roles))
        people_unspecified = len(self.get_people(
            Sex.unspecified, phenotype, phenotype_column, families,
            counter_roles))
        people_total = people_male + people_female + people_unspecified
        return {
            'people_male': people_male,
            'people_female': people_female,
            'people_unspecified': people_unspecified,
            'people_total': people_total,
            'phenotype': phenotype,
            'people_roles': list(map(str, counter_roles))
        }

    def get_families_with_phenotype(self, families, pheno, phenotype):
        if pheno is None:
            return dict(filter(
                lambda family:
                    len(family[1].get_family_phenotypes(phenotype['source']) -
                        set(phenotype['unaffected']['name'])) > 1,
                    families.items()))
        return dict(filter(
            lambda family:
                not (family[1].get_family_phenotypes(phenotype['source']) ^
                     set([pheno, phenotype['unaffected']['name']])),
                families.items()))

    def families_to_dataframe(self, families, phenotype_column):
        families_records = []
        for family in families.values():
            members = family.members_in_order
            families_records +=\
                [(member.family_id, member.sex.name, member.role.name,
                  member.status, member.layout_position, member.generated,
                  member.get_attr(phenotype_column)) for member in members]
        return pd.DataFrame.from_records(
            families_records,
            columns=['family_id', 'sex', 'role', 'status', 'layout_position',
                     'generated', 'phenotype'])

    def compare_families(self, first, second, phenotype_column):
        families = self.families_to_dataframe(
            {first.family_id: first, second.family_id: second},
            phenotype_column)

        grouped_families = families.groupby(
            ['sex', 'role', 'status', 'generated', 'phenotype'])

        for _, group in grouped_families:
            if len(group) == 2:
                continue
            elif group.size % 2 == 1:
                return False
            else:
                family_group = group.groupby(['family_id'])
                if group.shape[0] != (len(family_group.groups) * 2):
                    return False

        return families.shape[0] == (len(grouped_families.groups) * 2)

    def get_member_color(self, member, phenotype):
        if member.generated:
            return '#E0E0E0'
        else:
            pheno = member.get_attr(phenotype['source'])
            domain = phenotype['domain'].get(pheno, None)
            if domain and pheno:
                return domain['color']
            else:
                return phenotype['default']['color']

    def get_families_counters(self, pheno, phenotype, families):
        families = self.get_families_with_phenotype(families, pheno, phenotype)

        families_counters = {}
        for family_id, family in families.items():
            is_family_in_counters = False
            for unique_family in families_counters.keys():
                if self.compare_families(
                        family, unique_family, phenotype['source']):
                    is_family_in_counters = True
                    families_counters[unique_family] += 1
                    break
            if not is_family_in_counters:
                families_counters[family] = 1

        return {
            'counters': [
                {
                    'pedigree': [['family', 'person', 'father', 'mother',
                                  member.sex.short(),
                                  self.get_member_color(member, phenotype),
                                  member.layout_position, member.generated]
                                 for member in family.members_in_order],
                    'pedigrees_count': counter
                } for family, counter in families_counters.items()
            ],
            'phenotype': pheno
        }

    def get_families_report(self, query_object, phenotype):
        families_report = {}

        phenotype = self.phenotypes[phenotype]

        families = query_object.families
        phenotypes = list(query_object.get_phenotype_values(
            phenotype['source']))

        families_report['families_total'] = len(families)
        families_report['people_counters'] = []
        families_report['families_counters'] = []
        for pheno in phenotypes:
            for counter_roles in self.counters_roles:
                families_report['people_counters'].append(
                    self.get_people_counters(
                        pheno, phenotype['source'], families, counter_roles))
            families_report['families_counters'].append(
                    self.get_families_counters(pheno, phenotype, families))
        families_report['families_counters'].append(
            self.get_families_counters(None, phenotype, families))
        families_report['phenotypes'] = list(phenotypes)

        return families_report

    def get_effect_with_phenotype(
            self, query_object, effect, phenotype, phenotype_column,
            families_report, counter_roles):
        people_with_phenotype = []
        for family in query_object.families.values():
            people_with_phenotype +=\
                [person.person_id for person in
                    family.get_people_with_phenotype(
                        phenotype_column, phenotype)]

        variants_query = {
            'limit': None,
            'inheritance': 'denovo',
            'effect_types':
                self.effect_types_converter.get_effect_types(
                    effectTypes=effect),
            'roles': list(map(str, counter_roles)),
            'person_ids': people_with_phenotype
        }
        all_variants_query = {
            'limit': None,
            'inheritance': 'denovo',
            'roles': list(map(str, counter_roles))
        }
        variants = list(query_object.query_variants(**variants_query))
        all_variants = list(query_object.query_variants(**all_variants_query))

        events_people_count = set()
        for variant in variants:
            events_people_count.update(variant.variant_in_members)

        total_people = list(filter(
            lambda pc: pc['phenotype'] == phenotype,
            families_report['people_counters']))[0]['people_total']

        events_people_percent = len(events_people_count) / total_people\
            if total_people else 0
        events_rate_per_child = len(variants) / len(all_variants)\
            if len(all_variants) else 0

        return {
            'events_people_count': len(events_people_count),
            'events_people_percent': events_people_percent,
            'events_count': len(variants),
            'events_rate_per_child': events_rate_per_child,
            'phenotype': phenotype,
            'people_roles': list(map(str, counter_roles))
        }

    def get_effect(
            self, query_object, effect, phenotypes, phenotype_column,
            families_report):
        row = {}

        row['effect_type'] = effect
        row['row'] = []
        for phenotype in phenotypes:
            for counter_roles in self.counters_roles:
                row['row'].append(self.get_effect_with_phenotype(
                    query_object, effect, phenotype, phenotype_column,
                    families_report, counter_roles))

        return row

    def get_denovo_report(
            self, query_object, phenotype_column, families_report):
        denovo_report = {}

        phenotypes = list(query_object.get_phenotype_values(phenotype_column))
        effects = self.effect_groups + self.effect_types

        denovo_report['effect_groups'] = self.effect_groups
        denovo_report['effect_types'] = self.effect_types
        denovo_report['phenotype'] = phenotypes
        denovo_report['rows'] = []
        for effect in effects:
            denovo_report['rows'].append(self.get_effect(
                query_object, effect, phenotypes, phenotype_column,
                families_report))

        return denovo_report

    def get_common_reports(self, query_object):
        for qo, phenotype in query_object.items():
            common_reports = {}

            families_report = self.get_families_report(qo, phenotype)
            denovo_report = self.get_denovo_report(
                qo, self.phenotypes[phenotype]['source'], families_report)

            common_reports['families_report'] = families_report
            common_reports['denovo_report'] = denovo_report
            common_reports['name'] = qo.name

            yield common_reports

    def save_common_reports(self):
        studies = {self.study_facade.get_study(s): ph
                   for s, ph in self.studies.items()}
        study_groups = {self.study_group_facade.get_study_group(sg): ph
                        for sg, ph in self.study_groups.items()}
        for cr in self.get_common_reports(studies):
            with open(os.path.join(studies_common_reports_dir,
                      cr['name'] + '.json'), 'w') as crf:
                json.dump(cr, crf)
        for cr in self.get_common_reports(study_groups):
            with open(os.path.join(study_groups_common_reports_dir,
                      cr['name'] + '.json'), 'w') as crf:
                json.dump(cr, crf)


def main():
    crg = CommonReportsGenerator()
    crg.save_common_reports()


if __name__ == '__main__':
    main()
