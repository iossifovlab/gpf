from config import CommonReportsConfig
from study_groups.study_group_facade import StudyGroupFacade
from studies.study_facade import StudyFacade
from variants.attributes import Role, Sex


class CommonReportsGenerator(CommonReportsConfig):

    def __init__(self):
        super(CommonReportsGenerator, self).__init__()
        self.study_groups = self._study_groups()
        self.studies = self._studies()
        self.counters_roles = self._counters_roles()

        self.study_group_facade = StudyGroupFacade()
        self.study_facade = StudyFacade()

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

    def get_families_report(self, data):
        families_report = {}

        families = data.families
        phenotypes = data.phenotypes
        families_report['families_total'] = len(families)
        families_report['people_counters'] = []
        for phenotype in phenotypes:
            families_report['people_counters'].append(
                self.get_people_counters(
                    phenotype, phenotype_column, families))
        families_report['phenotypes'] = list(phenotypes)

        return families_report

    def get_common_reports(self, data):
        for d, phenotype_column in data.items():
            common_reports = {}

            common_reports['families_report'] = self.get_families_report(d)

            yield common_reports


def main():
    crg = CommonReportsGenerator()


if __name__ == '__main__':
    main()
