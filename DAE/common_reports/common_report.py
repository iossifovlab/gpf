import pandas as pd
import json
import os

from common_reports.config import CommonReportsConfig
from study_groups.study_group_facade import StudyGroupFacade
from studies.study_facade import StudyFacade
from variants.attributes import Role, Sex
from common.query_base import EffectTypesMixin
from studies.default_settings import get_config as get_studies_config
from study_groups.default_settings import get_config as get_study_groups_config


class PeopleCounter(object):

    def __init__(self, families, phenotype_info, phenotype, counter_roles):
        phenotype_source = phenotype_info['source']
        self.people_male = len(self._get_people(
            families, phenotype, phenotype_source, counter_roles, Sex.male))
        self.people_female = len(self._get_people(
            families, phenotype, phenotype_source, counter_roles, Sex.female))
        self.people_unspecified = len(self._get_people(
            families, phenotype, phenotype_source, counter_roles,
            Sex.unspecified))
        self.people_total =\
            self.people_male + self.people_female + self.people_unspecified
        self.phenotype = phenotype\
            if phenotype is not None else phenotype_info['default']['name']

    def to_dict(self):
        return {
            'people_male': self.people_male,
            'people_female': self.people_female,
            'people_unspecified': self.people_unspecified,
            'people_total': self.people_total,
            'phenotype': self.phenotype,
        }

    def _get_people(
            self, families, phenotype, phenotype_column, counter_roles, sex):
        people = []
        for family in families.values():
            people_with_role =\
                family.get_people_with_roles(counter_roles)
            people += list(filter(
                lambda pwr: pwr.sex == sex and
                pwr.get_attr(phenotype_column) == phenotype,
                people_with_role))
        return people


class PeopleCounters(object):

    def __init__(self, families, phenotype_info, phenotypes, counter_roles):
        self.roles = list(map(str, counter_roles))
        self.phenotypes = self._get_phenotypes(phenotype_info, phenotypes)
        self.counters = self._get_counters(
            families, phenotype_info, phenotypes, counter_roles)

    def to_dict(self):
        return {
            'roles': self.roles,
            'phenotypes': self.phenotypes,
            'counters': [c.to_dict() for c in self.counters],
        }

    def _get_counters(
            self, families, phenotype_info, phenotypes, counter_roles):
        return [
            PeopleCounter(families, phenotype_info, phenotype, counter_roles)
            for phenotype in phenotypes
        ]

    def _get_phenotypes(self, phenotype_info, phenotypes):
        return [
            phenotype if phenotype is not None
            else phenotype_info['default']['name']
            for phenotype in phenotypes
        ]


class FamilyCounter(object):

    def __init__(self, family, counter, phenotype_info):
        self.pedigree = self._get_pedigree(family, phenotype_info)
        self.pedigrees_count = counter

    def to_dict(self):
        return {
            'pedigree': self.pedigree,
            'pedigrees_count': self.pedigrees_count
        }

    def _get_member_color(self, member, phenotype_info):
        if member.generated:
            return '#E0E0E0'
        else:
            pheno = member.get_attr(phenotype_info['source'])
            domain = phenotype_info['domain'].get(pheno, None)
            if domain and pheno:
                return domain['color']
            else:
                return phenotype_info['default']['color']

    def _get_pedigree(self, family, phenotype_info):
        return [[member.family_id, member.person_id, member.dad, member.mom,
                 member.sex.short(), self._get_member_color(
                     member, phenotype_info),
                 member.layout_position, member.generated, '', '']
                for member in family.members_in_order]


class FamiliesCounter(object):

    def __init__(self, families, phenotype_info, phenotype):
        self.counters = self._get_counters(families, phenotype_info, phenotype)
        self.phenotype =\
            phenotype if phenotype is not None else phenotype_info['default']

    def to_dict(self):
        return {
            'counters': [c.to_dict() for c in self.counters],
            'phenotype': self.phenotype
        }

    def _get_families_with_phenotype(
            self, families, phenotype_info, phenotype):
        unaffected_phenotype = phenotype_info['unaffected']['name']\
            if phenotype != phenotype_info['unaffected']['name'] else -1
        if phenotype == -1:
            return dict(filter(lambda family: len(
                    family[1].get_family_phenotypes(phenotype_info['source']) -
                    set([unaffected_phenotype])
                ) > 1, families.items()))
        return dict(filter(
            lambda family: (len(
                (family[1].get_family_phenotypes(phenotype_info['source']) -
                 set([unaffected_phenotype]))
                ) == 1) and (phenotype in list(
                    family[1].get_family_phenotypes(phenotype_info['source'])
                )), families.items()))

    def _families_to_dataframe(self, families, phenotype_column):
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

    def _compare_families(self, first, second, phenotype_column):
        if len(first) != len(second):
            return False

        families = self._families_to_dataframe(
            {first.family_id: first, second.family_id: second},
            phenotype_column)

        grouped_families = families.groupby(
            ['sex', 'role', 'status', 'generated', 'phenotype'])

        for _, group in grouped_families:
            family_group = group.groupby(['family_id'])
            if len(family_group.groups) == 2:
                if len(family_group.groups[first.family_id]) !=\
                        len(family_group.groups[second.family_id]):
                    return False
            else:
                return False

        return True

    def _get_families_counters(self, families, phenotype_info, phenotype):
        families_with_phenotype = self._get_families_with_phenotype(
            families, phenotype_info, phenotype)

        families_counters = {}
        for family_id, family in families_with_phenotype.items():
            is_family_in_counters = False
            for unique_family in families_counters.keys():
                if self._compare_families(
                        family, unique_family, phenotype_info['source']):
                    is_family_in_counters = True
                    families_counters[unique_family] += 1
                    break
            if not is_family_in_counters:
                families_counters[family] = 1

        return families_counters

    def _get_counters(self, families, phenotype_info, phenotype):
        families_counters =\
            self._get_families_counters(families, phenotype_info, phenotype)
        return [FamilyCounter(family, counter, phenotype_info)
                for family, counter in families_counters.items()]


class FamiliesCounters(object):

    def __init__(self, families, phenotype_info, phenotypes):
        self.phenotypes = self._get_phenotypes(phenotype_info, phenotypes)
        self.counters =\
            self._get_counters(families, phenotype_info, phenotypes)

    def to_dict(self):
        return {
            'phenotypes': self.phenotypes,
            'counters': [counter.to_dict() for counter in self.counters]
        }

    def _get_counters(self, families, phenotype_info, phenotypes):
        return [FamiliesCounter(families, phenotype_info, phenotype)
                for phenotype in phenotypes + [-1]]

    def _get_phenotypes(self, phenotype_info, phenotypes):
        return [
            phenotype if phenotype is not None
            else phenotype_info['default']['name']
            for phenotype in phenotypes
        ]


class FamiliesReport(object):

    def __init__(
            self, query_object, phenotypes_info, phenotypes, counters_roles):
        families = query_object.families

        self.families_total = len(families)
        self.people_counters = self._get_people_counters(
            families, phenotypes_info, phenotypes, counters_roles)
        self.families_counters =\
            self._get_families_counters(families, phenotypes_info, phenotypes)

    def to_dict(self):
        return {
            'families_total': self.families_total,
            'people_counters': [pc.to_dict() for pc in self.people_counters],
            'families_counters':
                [fc.to_dict() for fc in self.families_counters]
        }

    def _get_people_counters(
            self, families, phenotypes_info, phenotypes, counters_roles):
        return [
            PeopleCounters(families, phenotype_info, phenotype, counter_roles)
            for phenotype_info, phenotype in zip(phenotypes_info, phenotypes)
            for counter_roles in counters_roles
        ]

    def _get_families_counters(self, families, phenotypes_info, phenotypes):
        return [
            FamiliesCounters(families, phenotype_info, phenotype)
            for phenotype_info, phenotype in zip(phenotypes_info, phenotypes)
        ]


class EffectWithPhenotype(object):

    def __init__(
            self, query_object, phenotype_info, phenotype, families_report,
            effect, counter_roles):
            effect_types_converter = EffectTypesMixin()

            people_with_phenotype = self._people_with_phenotype(
                query_object, phenotype_info, phenotype)

            variants = self._get_variants(
                query_object, people_with_phenotype, effect, counter_roles,
                effect_types_converter)
            all_variants = self._get_all_variants(query_object, counter_roles)

            events_people_count =\
                self._get_events_people_count(variants, people_with_phenotype)
            total_people = self._get_total_people(
                phenotype_info, phenotype, families_report)

            self.events_people_count = events_people_count
            self.events_people_percent =\
                (self.events_people_count / total_people)\
                if total_people else 0
            self.events_count = len(variants)
            self.events_rate_per_child =\
                (self.events_count / len(all_variants))\
                if len(all_variants) else 0

            self.phenotype = phenotype\
                if phenotype is not None else phenotype_info['default']['name']
            self.people_roles = list(map(str, counter_roles))

    def to_dict(self):
        return {
            'events_people_count': self.events_people_count,
            'events_people_percent': self.events_people_percent,
            'events_count': self.events_count,
            'events_rate_per_child': self.events_rate_per_child,
            'phenotype': self.phenotype,
            'people_roles': self.people_roles
        }

    def _people_with_phenotype(self, query_object, phenotype_info, phenotype):
        people_with_phenotype = set()

        for family in query_object.families.values():
            family_members_with_phenotype = set(
                [person.person_id for person in
                 family.get_people_with_phenotype(
                     phenotype_info['source'], phenotype)])
            people_with_phenotype.update(family_members_with_phenotype)

        return people_with_phenotype

    def _get_variants(
            self, query_object, people_with_phenotype, effect, counter_roles,
            effect_types_converter):
        variants_query = {
            'limit': None,
            'inheritance': 'denovo',
            'effect_types':
                effect_types_converter.get_effect_types(effectTypes=effect),
            'roles': list(map(str, counter_roles)),
            'person_ids': list(people_with_phenotype)
        }

        variants = list(query_object.query_variants(**variants_query))

        return variants

    def _get_all_variants(self, query_object, counter_roles):
        all_variants_query = {
            'limit': None,
            'inheritance': 'denovo',
            'roles': list(map(str, counter_roles))
        }

        all_variants = list(query_object.query_variants(**all_variants_query))

        return all_variants

    def _get_events_people_count(self, variants, people_with_phenotype):
        events_people = set()

        for variant in variants:
            events_people.update(
                (set(variant.variant_in_members) & people_with_phenotype))

        return len(events_people)

    def _get_total_people(
            self, phenotype_info, phenotype, families_report_with_roles):
        return list(filter(
            lambda pc: pc.phenotype == (phenotype if phenotype is not None else
                                        phenotype_info['default']['name']),
            families_report_with_roles.counters))[0].people_total


class Effect(object):

    def __init__(
            self, query_object, phenotype_info, phenotypes, families_report,
            effect, counter_roles):
        self.effect_type = effect
        self.row = self._get_row(
            query_object, phenotype_info, phenotypes, families_report, effect,
            counter_roles)

    def to_dict(self):
        return {
            'effect_type': self.effect_type,
            'row': [r.to_dict() for r in self.row],
        }

    def _get_row(
            self, query_object, phenotype_info, phenotypes, families_report,
            effect, counter_roles):
        return [EffectWithPhenotype(
            query_object, phenotype_info, phenotype, families_report, effect,
            counter_roles) for phenotype in phenotypes]


class DenovoReportTable(object):

    def __init__(
            self, query_object, phenotype_info, phenotypes, families_report,
            effects, counter_roles):
        self.phenotypes = self._get_phenotypes(phenotype_info, phenotypes)

        families_report = self._get_families_report(
            families_report, self.phenotypes, counter_roles)

        self.rows = self._get_rows(
            query_object, phenotype_info, phenotypes, families_report, effects,
            counter_roles)
        self.roles = list(map(str, counter_roles))

    def to_dict(self):
        return {
            'rows': [r.to_dict() for r in self.rows],
            'roles': self.roles,
            'phenotypes': self.phenotypes
        }

    def _get_families_report(self, families_report, phenotypes, counter_roles):
        return list(filter(
            lambda fr: (fr.phenotypes == phenotypes) and
            (fr.roles == list(map(str, counter_roles))),
            families_report.people_counters))[0]

    def _get_phenotypes(self, phenotype_info, phenotypes):
        return [
            phenotype if phenotype is not None
            else phenotype_info['default']['name']
            for phenotype in phenotypes
        ]

    def _get_rows(
            self, query_object, phenotype_info, phenotypes, families_report,
            effects, counter_roles):
        return [
            Effect(query_object, phenotype_info, phenotypes, families_report,
                   effect, counter_roles) for effect in effects
        ]


class DenovoReport(object):

    def __init__(
            self, query_object, phenotype_info, phenotypes, families_report,
            effect_groups, effect_types, counters_roles):
        effects = effect_groups + effect_types

        self.effect_groups = effect_groups
        self.effect_types = effect_types
        self.tables = self._get_tables(
            query_object, phenotype_info, phenotypes, families_report,
            effects, counters_roles)

    def to_dict(self):
        return {
            'effect_groups': self.effect_groups,
            'effect_types': self.effect_types,
            'tables': [t.to_dict() for t in self.tables]
        }

    def _get_tables(
            self, query_object, phenotypes_info, phenotypes, families_report,
            effects, counters_roles):
        return [DenovoReportTable(
            query_object, phenotype_info, phenotype, families_report, effects,
            counter_roles)
            for phenotype_info, phenotype in zip(phenotypes_info, phenotypes)
            for counter_roles in counters_roles
        ]


class CommonReport(object):

    def __init__(
            self, query_object, query_object_properties, phenotypes_info,
            counters_roles, effect_groups, effect_types):
        phenotypes_info = self._get_phenotypes_info(
            query_object_properties, phenotypes_info)
        phenotypes =\
            self._get_query_object_phenotypes(query_object, phenotypes_info)

        self.families_report = FamiliesReport(
            query_object, phenotypes_info, phenotypes, counters_roles)
        self.denovo_report = DenovoReport(
            query_object, phenotypes_info, phenotypes, self.families_report,
            effect_groups, effect_types, counters_roles)
        self.study_name = query_object.name
        self.phenotype = self._get_phenotype(phenotypes_info, phenotypes)
        self.study_type = ','.join(query_object.study_types)\
            if query_object.study_types else None
        self.study_year = ','.join(query_object.years)\
            if query_object.years else None
        self.pub_med = ','.join(query_object.pub_meds)\
            if query_object.pub_meds else None
        self.families = len(query_object.families)
        self.number_of_probands =\
            self._get_number_of_people_with_role(query_object, Role.prb)
        self.number_of_siblings =\
            self._get_number_of_people_with_role(query_object, Role.sib)
        self.denovo = query_object.has_denovo
        self.transmitted = query_object.has_transmitted
        self.study_description = query_object.description
        self.is_downloadable = query_object_properties['is_downloadable']

    def to_dict(self):
        return {
            'families_report': self.families_report.to_dict(),
            'denovo_report': self.denovo_report.to_dict(),
            'study_name': self.study_name,
            'phenotype': self.phenotype,
            'study_type': self.study_type,
            'study_year': self.study_year,
            'pub_med': self.pub_med,
            'families': self.families,
            'number_of_probands': self.number_of_probands,
            'number_of_siblings': self.number_of_siblings,
            'denovo': self.denovo,
            'transmitted': self.transmitted,
            'study_description': self.study_description,
            'is_downloadable': self.is_downloadable
        }

    def _get_phenotypes_info(self, query_object_properties, phenotypes_info):
        return [
            phenotypes_info[phenotype_group]
            for phenotype_group in query_object_properties['phenotype_groups']
        ]

    def _get_query_object_phenotypes(self, query_object, phenotypes_info):
        return [
            list(query_object.get_phenotype_values(phenotype_info['source']))
            for phenotype_info in phenotypes_info
        ]

    def _get_phenotype(self, phenotypes_info, phenotypes):
        default_phenotype = phenotypes_info[0]['default']['name']

        return [pheno if pheno is not None else default_phenotype
                for pheno in phenotypes[0]]

    def _get_number_of_people_with_role(self, query_object, role):
        return sum([len(family.get_people_with_role(role))
                    for family in query_object.families.values()])


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
        self.phenotypes_info = self.config.phenotypes()

        if study_facade is None:
            study_facade = StudyFacade()
        if study_group_facade is None:
            study_group_facade = StudyGroupFacade()

        self.study_facade = study_facade
        self.study_group_facade = study_group_facade

    def get_common_reports(self, query_object):
        for qo, qo_properties in query_object.items():
            yield CommonReport(
                qo, qo_properties, self.phenotypes_info, self.counters_roles,
                self.effect_groups, self.effect_types)

    def save_common_reports(self):
        studies = {self.study_facade.get_study(s): s_prop
                   for s, s_prop in self.studies.items()}
        study_groups = {self.study_group_facade.get_study_group(sg): sg_prop
                        for sg, sg_prop in self.study_groups.items()}
        studies_common_reports_dir = get_studies_config() \
            .get('COMMON_REPORTS_DIR')
        study_groups_common_reports_dir = get_study_groups_config() \
            .get('COMMON_REPORTS_DIR')
        for cr in self.get_common_reports(studies):
            with open(os.path.join(studies_common_reports_dir,
                      cr.study_name + '.json'), 'w') as crf:
                json.dump(cr.to_dict(), crf)
        for cr in self.get_common_reports(study_groups):
            with open(os.path.join(study_groups_common_reports_dir,
                      cr.study_name + '.json'), 'w') as crf:
                json.dump(cr.to_dict(), crf)
