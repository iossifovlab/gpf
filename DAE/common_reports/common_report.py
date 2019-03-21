from __future__ import unicode_literals
from __future__ import division

import os
import pandas as pd
import numpy as np
import json
import itertools
from collections import defaultdict, OrderedDict
from copy import deepcopy
# from utils.vcf_utils import mat2str

from variants.attributes import Role, Sex
from variants.family import FamiliesBase

from common.query_base import EffectTypesMixin


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

    def to_dict(self, rows):
        people_counter_dict =\
            OrderedDict([(row, getattr(self, row)) for row in rows])
        people_counter_dict['column'] = self.column
        return people_counter_dict

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
        return self.people_total == 0

    def is_empty_field(self, field):
        return getattr(self, field) == 0


class PeopleCounters(object):

    def __init__(self, families, filter_object):
        self.counters =\
            self._get_counters(families, filter_object)

        self.group_name = filter_object.name
        self.rows = self._get_rows(self.counters)
        self.columns = self._get_columns(self.counters)

    def to_dict(self):
        return OrderedDict([
            ('group_name', self.group_name),
            ('columns', self.columns),
            ('rows', self.rows),
            ('counters', [c.to_dict(self.rows) for c in self.counters])
        ])

    def _get_counters(self, families, filter_object):
        people_counters = [PeopleCounter(families, filters)
                           for filters in filter_object.filter_objects]

        return list(filter(
            lambda people_counter: not people_counter.is_empty(),
            people_counters))

    def _get_columns(self, people_counters):
        return [people_counter.column for people_counter in people_counters]

    def _is_row_empty(self, row, people_counters):
        return all([people_counter.is_empty_field(row)
                    for people_counter in people_counters])

    def _get_rows(self, people_counters):
        rows = ['people_male', 'people_female',
                'people_unspecified', 'people_total']
        return [row for row in rows
                if not self._is_row_empty(row, people_counters)]


class FamilyCounter(object):

    def __init__(self, family, counter, phenotype_info):
        self.pedigree = self._get_pedigree(family, phenotype_info)
        self.pedigrees_count = counter

    def to_dict(self):
        return OrderedDict([
            ('pedigree', self.pedigree),
            ('pedigrees_count', self.pedigrees_count)
        ])

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
        return [[member.family_id, member.person_id, member.dad_id,
                 member.mom_id, member.sex.short(), str(member.role),
                 self._get_member_color(member, phenotype_info),
                 member.layout_position, member.generated, '', '']
                for member in family.members_in_order]


class FamiliesCounter(object):

    def __init__(
            self, families, phenotype_info, draw_all_families,
            families_count_show_id):
        self.counters = self._get_counters(
            families, phenotype_info, draw_all_families,
            families_count_show_id)

    def to_dict(self):
        return OrderedDict([
            ('counters', [c.to_dict() for c in self.counters])
        ])

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
            OrderedDict([(first.family_id, first),
                         (second.family_id, second)]),
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

    def _get_unique_families_counters(self, families, phenotype_info):
        families_counters = OrderedDict()
        for family in families:
            is_family_in_counters = False
            for unique_family in families_counters.keys():
                if self._compare_families(
                        family, unique_family, phenotype_info.source):
                    is_family_in_counters = True
                    families_counters[unique_family].append(family.family_id)
                    break
            if not is_family_in_counters:
                families_counters[family] = [family.family_id]

        return families_counters

    def _get_all_families_counters(self, families):
        return OrderedDict([(family, family.family_id) for family in families])

    def _get_sorted_families_counters(
            self, families, phenotype_info, families_count_show_id):
        families_counters = self._get_unique_families_counters(
            families, phenotype_info)

        families_counters = OrderedDict(sorted(
            families_counters.items(), key=lambda fc: len(fc[1]),
            reverse=True))

        families_counters = OrderedDict([
            (family, (
                ', '.join(family_ids)
                if families_count_show_id is not None and
                families_count_show_id >= len(family_ids)
                else len(family_ids)))
            for family, family_ids in families_counters.items()
        ])

        return families_counters

    def _get_counters(
            self, families, phenotype_info, draw_all_families,
            families_count_show_id):
        if draw_all_families is True:
            families_counters = self._get_all_families_counters(families)
        else:
            families_counters = self._get_sorted_families_counters(
                families, phenotype_info, families_count_show_id)

        return [FamilyCounter(family, counter, phenotype_info)
                for family, counter in families_counters.items()]


class FamiliesCounters(object):

    def __init__(
            self, families, phenotype_info, draw_all_families,
            families_count_show_id):
        self.group_name = phenotype_info.name
        self.phenotypes = phenotype_info.get_phenotypes()
        self.counters = self._get_counters(
            families, phenotype_info, draw_all_families,
            families_count_show_id)
        self.legend = self._get_legend(phenotype_info)

    def to_dict(self):
        return OrderedDict([
            ('group_name', self.group_name),
            ('phenotypes', self.phenotypes),
            ('counters', [counter.to_dict() for counter in self.counters]),
            ('legend', self.legend)
        ])

    def _get_families_groups(self, families, phenotype_info):
        families_groups = defaultdict(list)

        for family in families.values():
            family_phenotypes =\
                frozenset(family.get_family_phenotypes(phenotype_info.source))
            family_phenotypes -= {phenotype_info.unaffected['name']}

            families_groups[family_phenotypes].append(family)

        families_groups_keys = sorted(list(families_groups.keys()), key=len)
        families_groups =\
            [families_groups[key] for key in families_groups_keys]

        return families_groups

    def _get_counters(
            self, families, phenotype_info, draw_all_families,
            families_count_show_id):

        families_groups =\
            self._get_families_groups(families, phenotype_info)

        return [FamiliesCounter(
            families, phenotype_info, draw_all_families,
            families_count_show_id)
                for families in families_groups]

    def _get_legend(self, phenotype_info):
        return list(phenotype_info.domain.values()) +\
            [phenotype_info.default] +\
            [phenotype_info.missing_person_info]


class FamiliesReport(object):

    def __init__(
            self, query_object, phenotypes_info, filter_objects,
            draw_all_families=False, families_count_show_id=False):
        families = query_object.families

        self.families_total = len(families)
        self.people_counters =\
            self._get_people_counters(families, filter_objects)
        self.families_counters = self._get_families_counters(
            families, phenotypes_info, draw_all_families,
            families_count_show_id)

    def to_dict(self):
        return OrderedDict([
            ('families_total', self.families_total),
            ('people_counters', [pc.to_dict() for pc in self.people_counters]),
            ('families_counters',
             [fc.to_dict() for fc in self.families_counters])
        ])

    def _get_people_counters(self, families, filter_objects):
        return [
            PeopleCounters(families, filter_object)
            for filter_object in filter_objects
        ]

    def _get_families_counters(
            self, families, phenotypes_info, draw_all_families,
            families_count_show_id):
        return [
            FamiliesCounters(families, phenotype_info, draw_all_families,
                             families_count_show_id)
            for phenotype_info in phenotypes_info.phenotypes_info
        ]


class EffectWithFilter(object):

    def __init__(self, study, denovo_variants, filter_object, effect):
        effect_types_converter = EffectTypesMixin()
        families_base = FamiliesBase()
        families_base.families = study.families

        people_with_filter =\
            self._people_with_filter(study, filter_object)
        people_with_parents = families_base.persons_with_parents()
        people_with_parents_ids =\
            set(families_base.persons_id(people_with_parents))

        variants = self._get_variants(
            study, denovo_variants, people_with_filter,
            people_with_parents_ids, effect, effect_types_converter)

        self.number_of_observed_events = len(variants)
        self.number_of_children_with_event =\
            self._get_number_of_children_with_event(
                variants, people_with_filter, people_with_parents_ids)
        self.observed_rate_per_child =\
            self.number_of_observed_events / len(people_with_parents_ids)\
            if len(people_with_parents_ids) != 0 else 0
        self.percent_of_children_with_events =\
            self.number_of_children_with_event / len(people_with_parents_ids)\
            if len(people_with_parents_ids) != 0 else 0

        self.column = filter_object.get_column()

    def to_dict(self):
        return OrderedDict([
            ('number_of_observed_events', self.number_of_observed_events),
            ('number_of_children_with_event',
             self.number_of_children_with_event),
            ('observed_rate_per_child', self.observed_rate_per_child),
            ('percent_of_children_with_events',
             self.percent_of_children_with_events),
            ('column', self.column)
        ])

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
            self, study, denovo_variants, people_with_filter, 
            people_with_parents,
            effect, effect_types_converter):
        people = people_with_filter.intersection(people_with_parents)
        effect_types = set(
            effect_types_converter.get_effect_types(effectTypes=effect))
        variants = []
        for v in denovo_variants:
            for aa in v.alt_alleles:
                if not (set(aa.variant_in_members) & people):
                    continue
                if not (aa.effect.types & effect_types):
                    continue
                variants.append(v)
                break
        return variants

    def _get_number_of_children_with_event(
            self, variants, people_with_filter, people_with_parents):
        children_with_event = set()

        for variant in variants:
            for va in variant.alt_alleles:
                children_with_event.update(
                    (set(va.variant_in_members) & people_with_filter &
                     people_with_parents))

        return len(children_with_event)

    def is_empty(self):
        return self.number_of_observed_events == 0 and\
            self.number_of_children_with_event == 0 and\
            self.observed_rate_per_child == 0 and\
            self.percent_of_children_with_events == 0


class Effect(object):

    def __init__(
            self, study, denovo_variants, effect, filter_objects):
        self.effect_type = effect
        self.row = self._get_row(
            study, denovo_variants, effect, filter_objects)

    def to_dict(self):
        return OrderedDict([
            ('effect_type', self.effect_type),
            ('row', [r.to_dict() for r in self.row])
        ])

    def _get_row(self, study, denovo_variants, effect, filter_objects):
        return [
            EffectWithFilter(study, denovo_variants, filter_object, effect)
            for filter_object in filter_objects.filter_objects]

    def is_row_empty(self):
        return all([value.is_empty() for value in self.row])

    def get_empty(self):
        return [value.is_empty() for value in self.row]

    def remove_elements(self, indexes):
        for index in sorted(indexes, reverse=True):
            self.row.pop(index)


class DenovoReportTable(object):

    def __init__(
            self, query_object, denovo_variants,
            effect_groups, effect_types, filter_object):
        effects = effect_groups + effect_types

        self.group_name = filter_object.name
        self.columns = filter_object.get_columns()

        self.effect_groups = effect_groups
        self.effect_types = effect_types

        self.rows = self._get_rows(
            query_object, denovo_variants, effects, filter_object)

    def to_dict(self):
        return OrderedDict([
            ('rows', [r.to_dict() for r in self.rows]),
            ('group_name', self.group_name),
            ('columns', self.columns),
            ('effect_groups', self.effect_groups),
            ('effect_types', self.effect_types),
        ])

    def _remove_empty_columns(self, indexes):
        for index in sorted(indexes, reverse=True):
            self.columns.pop(index)

    def _remove_empty_rows(self, effect_rows):
        for effect_row in effect_rows:
            if effect_row.is_row_empty():
                try:
                    self.effect_groups.remove(effect_row.effect_type)
                except ValueError:
                    pass
                try:
                    self.effect_types.remove(effect_row.effect_type)
                except ValueError:
                    pass

        return list(filter(
            lambda effect_row: not effect_row.is_row_empty(),
            effect_rows))

    def _get_rows(
            self, query_object, denovo_variants, effects, filter_object):

        effect_rows = [
            Effect(query_object, denovo_variants, effect, filter_object)
            for effect in effects]

        effect_rows_empty_columns = list(map(
            all, np.array([effect_row.get_empty()
                           for effect_row in effect_rows]).T))

        effect_rows_empty_columns_index =\
            list(np.where(effect_rows_empty_columns)[0])

        self._remove_empty_columns(effect_rows_empty_columns_index)

        for effect_row in effect_rows:
            effect_row.remove_elements(effect_rows_empty_columns_index)

        effect_rows = self._remove_empty_rows(effect_rows)

        return effect_rows

    def is_empty(self):
        return all([row.is_row_empty() for row in self.rows])


class DenovoReport(object):

    def __init__(
            self, query_object, effect_groups, effect_types, filter_objects):
        denovo_variants = query_object.query_variants(
            limit=None,
            inheritance='denovo',
        )
        denovo_variants = list(denovo_variants)

        self.tables = self._get_tables(
            query_object, denovo_variants, 
            effect_groups, effect_types, filter_objects)

    def to_dict(self):
        return OrderedDict([
            ('tables', [t.to_dict() for t in self.tables])
        ])

    def _get_tables(
            self, query_object, denovo_variants,
            effect_groups, effect_types, filter_objects):

        denovo_report_tables = []
        for filter_object in filter_objects:
            denovo_report_table = DenovoReportTable(
                query_object, denovo_variants,
                deepcopy(effect_groups), deepcopy(effect_types),
                filter_object)

            if not denovo_report_table.is_empty():
                denovo_report_tables.append(denovo_report_table)

        return denovo_report_tables

    def is_empty(self):
        return len(self.tables) == 0


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


class PhenotypeInfo(object):

    def __init__(
            self, phenotype_info, phenotype_group, query_object=None,
            phenotypes=None):
        self.name = phenotype_info['name']
        self.domain = phenotype_info['domain']
        self.unaffected = phenotype_info['unaffected']
        self.default = phenotype_info['default']
        self.source = phenotype_info['source']

        self.phenotypes = self._get_phenotypes(query_object)\
            if phenotypes is None else phenotypes

        self.phenotype_group = phenotype_group

    def _get_phenotypes(self, query_object):
        return list(query_object.get_pedigree_values(self.source))

    def get_phenotypes(self):
        return [
            phenotype if phenotype is not None else self.default['name']
            for phenotype in self.phenotypes
        ]

    @property
    def missing_person_info(self):
        return OrderedDict([
            ('id', 'missing-person'),
            ('name', 'missing-person'),
            ('color', '#E0E0E0')
        ])


class PhenotypesInfo(object):

    def __init__(self, query_object, filter_info, phenotypes_info):
        self.phenotypes_info = self._get_phenotypes_info(
            query_object, filter_info, phenotypes_info)

    def _get_phenotypes_info(
            self, query_object, filter_info, phenotypes_info):
        return [
            PhenotypeInfo(phenotypes_info[phenotype_group], phenotype_group,
                          query_object=query_object)
            for phenotype_group in filter_info['phenotype_groups']
        ]

    def get_first_phenotype_info(self):
        return self.phenotypes_info[0]

    def has_phenotype_info(self, phenotype_group):
        return len(list(filter(
            lambda phenotype_info:
            phenotype_info.phenotype_group == phenotype_group,
            self.phenotypes_info))) != 0

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
        self.filters.append(Filter(column, value))

    def get_column(self):
        return ' and '.join([filter.get_column() for filter in self.filters])

    @staticmethod
    def from_list(filters):
        return [FilterObject(list(filter)) for filter in filters]


class FilterObjects(object):

    def __init__(self, name, filter_objects=[]):
        self.name = name
        self.filter_objects = filter_objects

    def add_filter_object(self, filter_object):
        self.filter_objects.append(filter_object)

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
                    el_values = query_object.get_pedigree_values(el)

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
