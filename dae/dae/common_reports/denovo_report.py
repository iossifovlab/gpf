import numpy as np
from copy import deepcopy
from collections import OrderedDict

from dae.utils.effect_utils import EffectTypesMixin
from dae.variants.family import Family

class EffectCell(object):

    def __init__(self, study, denovo_variants, filter_object, effect):
        self.study = study
        self.denovo_variants = denovo_variants
        self.filter_object = filter_object
        self.effect = effect

        self.effect_types_converter = EffectTypesMixin()

        people_with_filter = self._people_with_filter()
        people_with_parents = Family.persons_with_parents(study.families)
        people_with_parents_ids =\
            set(Family.persons_ids(people_with_parents))

        variants = self._get_variants(
            people_with_filter, people_with_parents_ids)

        self.number_of_observed_events = len(variants)
        self.number_of_children_with_event = \
            self._get_number_of_children_with_event(
                variants, people_with_filter, people_with_parents_ids)
        self.observed_rate_per_child =\
            self.number_of_observed_events / len(people_with_parents_ids)\
            if len(people_with_parents_ids) != 0 else 0
        self.percent_of_children_with_events =\
            self.number_of_children_with_event / len(people_with_parents_ids)\
            if len(people_with_parents_ids) != 0 else 0

        self.column = self.filter_object.get_column_name()

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

    def _people_with_filter(self):
        people_with_filter = set()

        for family in self.study.families.values():
            family_members_with_filter = set.intersection(*[set(
                family.get_people_with_property(filt.column, filt.value))
                for filt in self.filter_object.filters])
            family_members_with_filter_ids =\
                [person.person_id for person in family_members_with_filter]
            people_with_filter.update(family_members_with_filter_ids)

        return people_with_filter

    def _get_variants(self, people_with_filter, people_with_parents):
        people = people_with_filter.intersection(people_with_parents)
        effect_types = set(self.effect_types_converter.get_effect_types(
            effectTypes=self.effect))
        variants = []
        for v in self.denovo_variants:
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


class EffectRow(object):

    def __init__(self, study, denovo_variants, effect, filter_objects):
        self.study = study
        self.denovo_variants = denovo_variants
        self.filter_objects = filter_objects

        self.effect_type = effect
        self.row = self._get_row()

    def to_dict(self):
        return OrderedDict([
            ('effect_type', self.effect_type),
            ('row', [r.to_dict() for r in self.row])
        ])

    def _get_row(self):
        return [
            EffectCell(
                self.study, self.denovo_variants, filter_object,
                self.effect_type)
            for filter_object in self.filter_objects.filter_objects]

    def is_row_empty(self):
        return all([value.is_empty() for value in self.row])

    def get_empty(self):
        return [value.is_empty() for value in self.row]

    def remove_elements(self, indexes):
        for index in sorted(indexes, reverse=True):
            self.row.pop(index)


class DenovoReportTable(object):

    def __init__(
            self, study, denovo_variants, effect_groups, effect_types,
            filter_object):
        self.study = study
        self.denovo_variants = denovo_variants
        self.filter_object = filter_object

        self.effects = effect_groups + effect_types

        self.group_name = filter_object.name
        self.columns = filter_object.get_columns()

        self.effect_groups = effect_groups
        self.effect_types = effect_types

        self.rows = self._get_rows()

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

    def _get_rows(self):

        effect_rows = [
            EffectRow(
                self.study, self.denovo_variants, effect, self.filter_object)
            for effect in self.effects
        ]

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

    def __init__(self, study, effect_groups, effect_types, filter_objects):
        self.study = study
        self.effect_groups = effect_groups
        self.effect_types = effect_types
        self.filter_objects = filter_objects

        denovo_variants = study.query_variants(
            limit=None,
            inheritance='denovo',
        )
        self.denovo_variants = list(denovo_variants)

        self.tables = self._get_tables()

    def to_dict(self):
        return OrderedDict([
            ('tables', [t.to_dict() for t in self.tables])
        ])

    def _get_tables(self):
        if len(self.denovo_variants) == 0:
            return []

        denovo_report_tables = []
        for filter_object in self.filter_objects:
            denovo_report_table = DenovoReportTable(
                self.study, self.denovo_variants, deepcopy(self.effect_groups),
                deepcopy(self.effect_types), filter_object)

            if not denovo_report_table.is_empty():
                denovo_report_tables.append(denovo_report_table)

        return denovo_report_tables

    def is_empty(self):
        return len(self.tables) == 0
