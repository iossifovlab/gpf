from config import CommonReportsConfig
from study_groups.study_group_facade import StudyGroupFacade
from studies.study_facade import StudyFacade
from variants.attributes import Role, Sex, Inheritance
from common.query_base import EffectTypesMixin


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

    def get_people(self, sex, phenotype, phenotype_column, families):
        people = []
        for family in families.values():
            people_with_role =\
                family.get_people_with_roles(self.counters_roles)
            people += list(filter(
                lambda pwr: pwr.sex == sex and
                pwr.get_attr(phenotype_column) == phenotype,
                people_with_role))
        return people

    def get_people_counters(self, phenotype, phenotype_column, families):
        people_male = len(self.get_people(
            Sex.male, phenotype, phenotype_column, families))
        people_female = len(self.get_people(
            Sex.female, phenotype, phenotype_column, families))
        people_unspecified = len(self.get_people(
            Sex.unspecified, phenotype, phenotype_column, families))
        people_total = people_male + people_female + people_unspecified
        return {
            'people_male': people_male,
            'people_female': people_female,
            'people_unspecified': people_unspecified,
            'people_total': people_total,
            'phenotype': phenotype,
            'people_roles': self.counters_roles
        }

    def get_families_report(self, data, phenotype):
        families_report = {}

        phenotype = self.phenotypes[phenotype]

        families = data.families
        phenotypes = list(data.get_phenotype_values(phenotype['source']))

        families_report['families_total'] = len(families)
        families_report['people_counters'] = []
        for pheno in phenotypes:
            families_report['people_counters'].append(
                self.get_people_counters(pheno, phenotype['source'], families))
        families_report['phenotypes'] = list(phenotypes)

        return families_report

    def get_effect_with_phenotype(
            self, data, effect, phenotype, phenotype_column, families_report):
        people_with_phenotype = []
        for family in data.families.values():
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
            'roles': list(map(str, self.counters_roles)),
            'person_ids': people_with_phenotype
        }
        all_variants_query = {
            'limit': None,
            'inheritance': 'denovo',
            'roles': list(map(str, self.counters_roles))
        }
        variants = list(data.query_variants(**variants_query))
        all_variants = list(data.query_variants(**all_variants_query))

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
            'people_roles': self.counters_roles
        }

    def get_effect(
            self, data, effect, phenotypes, phenotype_column, families_report):
        row = {}

        row['effect_type'] = effect
        row['row'] = []
        for phenotype in phenotypes:
            row['row'].append(self.get_effect_with_phenotype(
                data, effect, phenotype, phenotype_column, families_report))

        return row

    def get_denovo_report(self, data, phenotype_column, families_report):
        denovo_report = {}

        phenotypes = list(data.get_phenotype_values(phenotype_column))
        effects = self.effect_groups + self.effect_types

        denovo_report['effect_groups'] = self.effect_groups
        denovo_report['effect_types'] = self.effect_types
        denovo_report['phenotype'] = phenotypes
        denovo_report['rows'] = []
        for effect in effects:
            denovo_report['rows'].append(self.get_effect(
                data, effect, phenotypes, phenotype_column, families_report))

        return denovo_report

    def get_common_reports(self, data):
        for d, phenotype_column in data.items():
            common_reports = {}

            families_report = self.get_families_report(d, phenotype_column)
            denovo_report = self.get_denovo_report(
                d, phenotype_column, families_report)

            common_reports['families_report'] = families_report
            common_reports['denovo_report'] = denovo_report

            yield common_reports


def main():
    crg = CommonReportsGenerator()


if __name__ == '__main__':
    main()
