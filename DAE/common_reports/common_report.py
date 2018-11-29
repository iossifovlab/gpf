import pandas as pd
import json
import os

from common_reports.config import CommonReportsConfig
from study_groups.study_group_facade import StudyGroupFacade
from studies.study_facade import StudyFacade
from variants.attributes import Role, Sex, Inheritance
from common.query_base import EffectTypesMixin
from studies.default_settings import COMMON_REPORTS_DIR\
    as studies_common_reports_dir
from study_groups.default_settings import COMMON_REPORTS_DIR\
    as study_groups_common_reports_dir


class CommonReportsGenerator(object):

    def __init__(
            self, config=None, study_facade=None, study_group_facade=None):
        if config is None:
            config = CommonReportsConfig()

        self.config = config

        self.study_groups = self.config.study_groups()
        self.studies = self.config.studies()
        self.counters_roles = self.config.counters_roles()
        self.effect_groups = self.config.effect_groups()
        self.effect_types = self.config.effect_types()
        self.phenotypes = self.config.phenotypes()

        if study_facade is None:
            study_facade = StudyFacade()
        if study_group_facade is None:
            study_group_facade = StudyGroupFacade()

        self.study_facade = study_facade
        self.study_group_facade = study_group_facade

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
            self, pheno, phenotype, families, counter_roles):
        people_male = len(self.get_people(
            Sex.male, pheno, phenotype['source'], families, counter_roles))
        people_female = len(self.get_people(
            Sex.female, pheno, phenotype['source'], families, counter_roles))
        people_unspecified = len(self.get_people(
            Sex.unspecified, pheno, phenotype['source'], families,
            counter_roles))
        people_total = people_male + people_female + people_unspecified
        return {
            'people_male': people_male,
            'people_female': people_female,
            'people_unspecified': people_unspecified,
            'people_total': people_total,
            'phenotype':
                pheno if pheno is not None else phenotype['default']['name'],
            'people_roles': list(map(str, counter_roles))
        }

    def get_families_with_phenotype(self, families, pheno, phenotype):
        unaffected_phenotype = phenotype['unaffected']['name']\
            if pheno != phenotype['unaffected']['name'] else -1
        if pheno == -1:
            return dict(filter(
                lambda family:
                    len(family[1].get_family_phenotypes(phenotype['source']) -
                        set([unaffected_phenotype])) > 1, families.items()))
        return dict(filter(
            lambda family:
                len((family[1].get_family_phenotypes(phenotype['source']) -
                    set([unaffected_phenotype]))) == 1 and
                pheno in list(family[1].get_family_phenotypes(
                    phenotype['source'])),
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
        families_with_phenotype =\
            self.get_families_with_phenotype(families, pheno, phenotype)

        families_counters = {}
        for family_id, family in families_with_phenotype.items():
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
                    'pedigree':
                    [[member.family_id, member.person_id, member.dad,
                      member.mom, member.sex.short(),
                      self.get_member_color(member, phenotype),
                      member.layout_position, member.generated, '', '']
                     for member in family.members_in_order],
                    'pedigrees_count': counter
                } for family, counter in families_counters.items()
            ],
            'phenotype': pheno if pheno is not None else phenotype['default']
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
        for counter_roles in self.counters_roles:
            people_counters = {}
            people_counters['counters'] = []
            people_counters['roles'] = list(map(str, counter_roles))
            for pheno in phenotypes:
                people_counters['counters'].append(self.get_people_counters(
                    pheno, phenotype, families, counter_roles))
            families_report['people_counters'].append(people_counters)
        for pheno in phenotypes:
            families_report['families_counters'].append(
                    self.get_families_counters(pheno, phenotype, families))

        families_report['families_counters'].append(
            self.get_families_counters(-1, phenotype, families))
        families_report['phenotypes'] =\
            [pheno if pheno is not None else phenotype['default']['name']
             for pheno in phenotypes]

        return families_report

    def get_effect_with_phenotype(
            self, query_object, effect, pheno, phenotype,
            families_report, counter_roles):
        people_with_phenotype = set()
        for family in query_object.families.values():
            people_with_phenotype.update(
                set([person.person_id for person in
                     family.get_people_with_phenotype(
                         phenotype['source'], pheno)]))

        variants_query = {
            'limit': None,
            'inheritance': 'denovo',
            'effect_types':
                self.effect_types_converter.get_effect_types(
                    effectTypes=effect),
            'roles': list(map(str, counter_roles)),
            'person_ids': list(people_with_phenotype)
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
            events_people_count.update(
                (set(variant.variant_in_members) & people_with_phenotype))
        families_report_with_roles = list(filter(
            lambda fr: fr['roles'] == list(map(str, counter_roles)),
            families_report['people_counters']))[0]
        total_people = list(filter(
            lambda pc: pc['phenotype'] == (pheno if pheno is not None else
                                           phenotype['default']['name']),
            families_report_with_roles['counters']))[0]['people_total']

        events_people_percent = len(events_people_count) / total_people\
            if total_people else 0
        events_rate_per_child = len(variants) / len(all_variants)\
            if len(all_variants) else 0

        return {
            'events_people_count': len(events_people_count),
            'events_people_percent': events_people_percent,
            'events_count': len(variants),
            'events_rate_per_child': events_rate_per_child,
            'phenotype':
                pheno if pheno is not None else phenotype['default']['name'],
            'people_roles': list(map(str, counter_roles))
        }

    def get_effect(
            self, query_object, effect, phenotypes, phenotype,
            families_report, counter_roles):
        row = {}

        row['effect_type'] = effect
        row['row'] = []
        for pheno in phenotypes:
            row['row'].append(self.get_effect_with_phenotype(
                query_object, effect, pheno, phenotype,
                families_report, counter_roles))

        return row

    def get_denovo_report(
            self, query_object, phenotype, families_report):
        denovo_report = {}

        phenotypes =\
            list(query_object.get_phenotype_values(phenotype['source']))
        effects = self.effect_groups + self.effect_types

        denovo_report['effect_groups'] = self.effect_groups
        denovo_report['effect_types'] = self.effect_types
        denovo_report['phenotypes'] =\
            [pheno if pheno is not None else phenotype['default']['name']
             for pheno in phenotypes]
        denovo_report['tables'] = []
        for counter_roles in self.counters_roles:
            rows = {}
            rows['rows'] = []
            rows['roles'] = list(map(str, counter_roles))
            for effect in effects:
                rows['rows'].append(self.get_effect(
                    query_object, effect, phenotypes, phenotype,
                    families_report, counter_roles))
            denovo_report['tables'].append(rows)

        return denovo_report

    def get_common_reports(self, query_object):
        for qo, qo_properties in query_object.items():
            common_reports = {}

            families_report =\
                self.get_families_report(qo, qo_properties['phenotype'])
            denovo_report = self.get_denovo_report(
                qo, self.phenotypes[qo_properties['phenotype']],
                families_report)

            common_reports['families_report'] = families_report
            common_reports['denovo_report'] = denovo_report
            common_reports['study_name'] = qo.name
            common_reports['phenotype'] = ','.join(
                [pheno if pheno is not None else
                 self.phenotypes[qo_properties['phenotype']]['default']['name']
                 for pheno in qo.get_phenotype_values(
                     self.phenotypes[qo_properties['phenotype']]['source'])])
            common_reports['study_type'] =\
                ','.join(qo.study_types) if qo.study_types else None
            common_reports['study_year'] =\
                ','.join(qo.years) if qo.years else None
            common_reports['pub_med'] =\
                ','.join(qo.pub_meds) if qo.pub_meds else None
            common_reports['families'] = len(qo.families)
            common_reports['number_of_probands'] =\
                sum([len(family.get_people_with_role(Role.prb))
                     for family in qo.families.values()])
            common_reports['number_of_siblings'] =\
                sum([len(family.get_people_with_role(Role.sib))
                     for family in qo.families.values()])
            common_reports['denovo'] = qo.has_denovo
            common_reports['transmitted'] = qo.has_transmitted
            common_reports['study_description'] = qo.description
            common_reports['is_downloadable'] =\
                qo_properties['is_downloadable']

            yield common_reports

    def save_common_reports(self):
        studies = {self.study_facade.get_study(s): s_prop
                   for s, s_prop in self.studies.items()}
        study_groups = {self.study_group_facade.get_study_group(sg): sg_prop
                        for sg, sg_prop in self.study_groups.items()}
        for cr in self.get_common_reports(studies):
            with open(os.path.join(studies_common_reports_dir,
                      cr['study_name'] + '.json'), 'w') as crf:
                json.dump(cr, crf)
        for cr in self.get_common_reports(study_groups):
            with open(os.path.join(study_groups_common_reports_dir,
                      cr['study_name'] + '.json'), 'w') as crf:
                json.dump(cr, crf)


def main():
    crg = CommonReportsGenerator()
    crg.save_common_reports()


if __name__ == '__main__':
    main()
