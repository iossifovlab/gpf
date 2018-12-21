import pandas as pd
import numpy as np
import json
import os
import itertools

from common_reports.config import CommonReportsConfig
from study_groups.study_group_facade import StudyGroupFacade
from studies.study_facade import StudyFacade
from variants.attributes import Role, Sex
from common.query_base import EffectTypesMixin
from studies.default_settings import get_config as get_studies_config
from study_groups.default_settings import get_config as get_study_groups_config
from variants.family import FamiliesBase


class PeopleCounter(object):

    def __init__(self, families, filter_object):
        self.people_male =\
            len(self._get_people(families, filter_object, Sex.male))
        self.people_female =\
            len(self._get_people(families, filter_object, Sex.female))
        self.people_unspecified =\
            len(self._get_people(families, filter_object, Sex.unspecified))
        self.people_total =\
            self.people_male + self.people_female + self.people_unspecified
        self.column = filter_object.get_column()

    def to_dict(self):
        return {
            'people_male': self.people_male,
            'people_female': self.people_female,
            'people_unspecified': self.people_unspecified,
            'people_total': self.people_total,
            'column': self.column,
        }

    def _get_people(self, families, filter_object, sex):
        people = []

        for family in families.values():
            people += list(filter(
                lambda pwr: pwr.sex == sex and
                all([pwr.get_attr(filter.column) == filter.value
                     for filter in filter_object.filters]),
                family.members_in_order))

        return people

    def is_empty(self):
        return True if self.people_total == 0 else False


class PeopleCounters(object):

    def __init__(self, families, filter_object):
        self.counters =\
            self._get_counters(families, filter_object)

        self.group_name = filter_object.name
        self.columns = self._get_columns(self.counters)

    def to_dict(self):
        return {
            'group_name': self.group_name,
            'columns': self.columns,
            'counters': [c.to_dict() for c in self.counters],
        }

    def _get_counters(self, families, filter_object):
        people_counters = [PeopleCounter(families, filters)
                           for filters in filter_object.filter_objects]

        return list(filter(
            lambda people_counter: not people_counter.is_empty(),
            people_counters))

    def _get_columns(self, people_counters):
        return [people_counter.column for people_counter in people_counters]


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
            pheno = member.get_attr(phenotype_info.source)
            domain = phenotype_info.domain.get(pheno, None)
            if domain and pheno:
                return domain['color']
            else:
                return phenotype_info.default['color']

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
            phenotype if phenotype is not None else phenotype_info.default

    def to_dict(self):
        return {
            'counters': [c.to_dict() for c in self.counters],
            'phenotype': self.phenotype
        }

    def _get_families_with_phenotype(
            self, families, phenotype_info, phenotype):
        unaffected_phenotype = phenotype_info.unaffected['name']\
            if phenotype != phenotype_info.unaffected['name'] else -1
        if phenotype == -1:
            return dict(filter(lambda family: len(
                    family[1].get_family_phenotypes(phenotype_info.source) -
                    set([unaffected_phenotype])
                ) > 1, families.items()))
        return dict(filter(
            lambda family: (len(
                (family[1].get_family_phenotypes(phenotype_info.source) -
                 set([unaffected_phenotype]))
                ) == 1) and (phenotype in list(
                    family[1].get_family_phenotypes(phenotype_info.source)
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
                        family, unique_family, phenotype_info.source):
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

    def __init__(self, families, phenotype_info):
        self.group_name = phenotype_info.name
        self.phenotypes = phenotype_info.get_phenotypes()
        self.counters = self._get_counters(families, phenotype_info)

    def to_dict(self):
        return {
            'group_name': self.group_name,
            'phenotypes': self.phenotypes,
            'counters': [counter.to_dict() for counter in self.counters]
        }

    def _get_counters(self, families, phenotype_info):
        return [FamiliesCounter(families, phenotype_info, phenotype)
                for phenotype in phenotype_info.phenotypes + [-1]]


class FamiliesReport(object):

    def __init__(self, query_object, phenotypes_info, filter_objects):
        families = query_object.families

        self.families_total = len(families)
        self.people_counters =\
            self._get_people_counters(families, filter_objects)
        self.families_counters =\
            self._get_families_counters(families, phenotypes_info)

    def to_dict(self):
        return {
            'families_total': self.families_total,
            'people_counters': [pc.to_dict() for pc in self.people_counters],
            'families_counters':
                [fc.to_dict() for fc in self.families_counters]
        }

    def _get_people_counters(self, families, filter_objects):
        return [
            PeopleCounters(families, filter_object)
            for filter_object in filter_objects
        ]

    def _get_families_counters(self, families, phenotypes_info):
        return [
            FamiliesCounters(families, phenotype_info)
            for phenotype_info in phenotypes_info.phenotypes_info
        ]


class EffectWithFilter(object):

    def __init__(self, query_object, filter_object, effect):
        effect_types_converter = EffectTypesMixin()
        families_base = FamiliesBase()
        families_base.families = query_object.families

        people_with_filter =\
            self._people_with_filter(query_object, filter_object)
        people_with_parents = families_base.persons_with_parents()
        people_with_parents_ids =\
            set(families_base.persons_id(people_with_parents))

        variants = self._get_variants(
            query_object, people_with_filter, people_with_parents_ids,
            effect, effect_types_converter)

        self.number_of_observed_events = len(variants)
        self.number_of_children_with_event =\
            self._get_number_of_children_with_event(
                variants, people_with_filter, people_with_parents_ids)
        self.observed_rate_per_child = self.number_of_observed_events /\
            len(people_with_parents_ids)
        self.percent_of_children_with_events =\
            self.number_of_children_with_event / len(people_with_parents_ids)

        self.column = filter_object.get_column()

    def to_dict(self):
        return {
            'number_of_observed_events': self.number_of_observed_events,
            'number_of_children_with_event':
                self.number_of_children_with_event,
            'observed_rate_per_child': self.observed_rate_per_child,
            'percent_of_children_with_events':
                self.percent_of_children_with_events,
            'column': self.column
        }

    def _people_with_filter(self, query_object, filter_object):
        people_with_filter = set()

        for family in query_object.families.values():
            family_members_with_filter = set.intersection(*[set(
                family.get_people_with_property(filter.column, filter.value))
                for filter in filter_object.filters])
            family_members_with_filter_ids =\
                [person.person_id for person in family_members_with_filter]
            people_with_filter.update(family_members_with_filter_ids)

        return people_with_filter

    def _get_variants(
            self, query_object, people_with_filter, people_with_parents,
            effect, effect_types_converter):
        variants_query = {
            'limit': None,
            'inheritance': 'denovo',
            'effect_types':
                effect_types_converter.get_effect_types(effectTypes=effect),
            'person_ids':
                list(people_with_filter.intersection(people_with_parents))
        }

        variants = list(query_object.query_variants(**variants_query))

        return variants

    def _get_number_of_children_with_event(
            self, variants, people_with_filter, people_with_parents):
        children_with_event = set()

        for variant in variants:
            children_with_event.update(
                (set(variant.variant_in_members) & people_with_filter &
                 people_with_parents))

        return len(children_with_event)

    def is_empty(self):
        return True if self.number_of_observed_events == 0 and\
            self.number_of_children_with_event == 0 and\
            self.observed_rate_per_child == 0 and\
            self.percent_of_children_with_events == 0 else False


class Effect(object):

    def __init__(
            self, query_object, effect, filter_objects):
        self.effect_type = effect
        self.row = self._get_row(query_object, effect, filter_objects)

    def to_dict(self):
        return {
            'effect_type': self.effect_type,
            'row': [r.to_dict() for r in self.row],
        }

    def _get_row(self, query_object, effect, filter_objects):
        return [EffectWithFilter(query_object, filter_object, effect)
                for filter_object in filter_objects.filter_objects]

    def get_empty(self):
        return [value.is_empty() for value in self.row]

    def remove_elements(self, indexes):
        for index in sorted(indexes, reverse=True):
            self.row.pop(index)


class DenovoReportTable(object):

    def __init__(self, query_object, effects, filter_object):
        self.group_name = filter_object.name
        self.columns = filter_object.get_columns()

        self.rows = self._get_rows(query_object, effects, filter_object)

    def to_dict(self):
        return {
            'rows': [r.to_dict() for r in self.rows],
            'group_name': self.group_name,
            'columns': self.columns
        }

    def _remove_empty_columns(self, indexes):
        for index in sorted(indexes, reverse=True):
            self.columns.pop(index)

    def _get_rows(self, query_object, effects, filter_object):
        effect_rows = [Effect(query_object, effect, filter_object)
                       for effect in effects]

        effect_rows_empty_columns = list(map(
            all, np.array([effect_row.get_empty()
                           for effect_row in effect_rows]).T))

        effect_rows_empty_columns_index =\
            list(np.where(effect_rows_empty_columns)[0])

        self._remove_empty_columns(effect_rows_empty_columns_index)

        for effect_row in effect_rows:
            effect_row.remove_elements(effect_rows_empty_columns_index)

        return effect_rows


class DenovoReport(object):

    def __init__(
            self, query_object, effect_groups, effect_types, filter_objects):
        effects = effect_groups + effect_types

        self.effect_groups = effect_groups
        self.effect_types = effect_types
        self.tables = self._get_tables(
            query_object, effects, filter_objects)

    def to_dict(self):
        return {
            'effect_groups': self.effect_groups,
            'effect_types': self.effect_types,
            'tables': [t.to_dict() for t in self.tables]
        }

    def _get_tables(self, query_object, effects, filter_objects):
        return [DenovoReportTable(query_object, effects, filter_object)
                for filter_object in filter_objects]


class CommonReport(object):

    def __init__(
            self, query_object, query_object_properties, phenotypes_info,
            effect_groups, effect_types):
        phenotypes_info = PhenotypesInfo(
            query_object, query_object_properties, phenotypes_info)

        filter_objects = FilterObjects.get_filter_objects(
            query_object, phenotypes_info, query_object_properties['groups'])

        self.families_report =\
            FamiliesReport(query_object, phenotypes_info, filter_objects)
        self.denovo_report = DenovoReport(
            query_object, effect_groups, effect_types, filter_objects)
        self.study_name = query_object.name
        self.phenotype = self._get_phenotype(phenotypes_info)
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

    def _get_phenotype(self, phenotypes_info):
        phenotype_info = phenotypes_info.get_first_phenotype_info()
        default_phenotype = phenotype_info.default['name']

        return [pheno if pheno is not None else default_phenotype
                for pheno in phenotype_info.phenotypes]

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
                qo, qo_properties, self.phenotypes_info, self.effect_groups,
                self.effect_types)

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


class PhenotypeInfo(object):

    def __init__(self, query_object, phenotype_info, phenotype_group):
        self.name = phenotype_info['name']
        self.domain = phenotype_info['domain']
        self.unaffected = phenotype_info['unaffected']
        self.default = phenotype_info['default']
        self.source = phenotype_info['source']

        self.phenotypes = self._get_phenotypes(query_object)

        self.phenotype_group = phenotype_group

    def _get_phenotypes(self, query_object):
        return list(query_object.get_phenotype_values(self.source))

    def get_phenotypes(self):
        return [
            phenotype if phenotype is not None else self.default['name']
            for phenotype in self.phenotypes
        ]


class PhenotypesInfo(object):

    def __init__(self, query_object, query_object_properties, phenotypes_info):
        self.phenotypes_info = self._get_phenotypes_info(
            query_object, query_object_properties, phenotypes_info)

    def _get_phenotypes_info(
            self, query_object, query_object_properties, phenotypes_info):
        return [
            PhenotypeInfo(query_object, phenotypes_info[phenotype_group],
                          phenotype_group)
            for phenotype_group in query_object_properties['phenotype_groups']
        ]

    def get_first_phenotype_info(self):
        return self.phenotypes_info[0]

    def has_phenotype_info(self, phenotype_group):
        return True if len(list(filter(
            lambda phenotype_info:
            phenotype_info.phenotype_group == phenotype_group,
            self.phenotypes_info))) else False

    def get_phenotype_info(self, phenotype_group):
        return list(filter(
            lambda phenotype_info:
            phenotype_info.phenotype_group == phenotype_group,
            self.phenotypes_info))[0]


class Filter(object):

    def __init__(self, column, value, column_value=None):
        self.column = column
        self.value = value
        self.column_value =\
            column_value if column_value is not None else value

    def get_column(self):
        return str(self.column_value)


class FilterObject(object):

    def __init__(self, filters=[]):
        self.filters = filters

    def add_filter(self, column, value):
        self.filters.append(column, value)

    def get_column(self):
        return ' and '.join([filter.get_column() for filter in self.filters])

    @staticmethod
    def from_list(filters):
        return [FilterObject(list(filter)) for filter in filters]


class FilterObjects(object):

    def __init__(self, name, filter_objects=[]):
        self.name = name
        self.filter_objects = filter_objects

    def get_columns(self):
        return [filter_object.get_column()
                for filter_object in self.filter_objects]

    @staticmethod
    def get_filter_objects(query_object, phenotypes_info, groups):
        filter_objects = []
        for name, group in groups.items():
            filters = []
            for el in group:
                if phenotypes_info.has_phenotype_info(el):
                    phenotype_info = phenotypes_info.get_phenotype_info(el)
                    el_column = phenotype_info.source
                    el_values = phenotype_info.phenotypes
                else:
                    el_column = el
                    el_values = query_object.get_column_values(el)

                filter = []
                for el_value in el_values:
                    if phenotypes_info.has_phenotype_info(el) and\
                            el_value is None:
                        phenotype_info = phenotypes_info.get_phenotype_info(el)
                        filter.append(Filter(el_column, el_value,
                                             phenotype_info.default['name']))
                    else:
                        filter.append(Filter(el_column, el_value))
                filters.append(filter)

            filter_objects.append(FilterObjects(name, FilterObject.from_list(
                list(itertools.product(*filters)))))

        return filter_objects
