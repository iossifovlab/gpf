import time
import numpy as np
from copy import deepcopy
from collections import OrderedDict

from dae.utils.effect_utils import EffectTypesMixin
from dae.common_reports.people_filters import PeopleFilter


class EffectCell:
    def __init__(self, genotype_data, denovo_variants, people_filter, effect):
        self.genotype_data = genotype_data
        self.families = genotype_data.families
        self.denovo_variants = denovo_variants
        assert isinstance(people_filter, PeopleFilter)
        assert len(people_filter.people_with_filter_ids) > 0
        self.people_filter = people_filter
        self.effect = effect
        self.effect_types = set(
            EffectTypesMixin().get_effect_types(effectTypes=effect)
        )

        self.observed_variants_ids = set()
        self.observed_people_with_event = set([])

    @property
    def people_with_filter_ids(self):
        return self.people_filter.people_with_filter_ids

    @property
    def number_of_observed_events(self):
        return len(self.observed_variants_ids)

    @property
    def number_of_children_with_event(self):
        return len(self.observed_people_with_event)

    @property
    def number_of_people_with_filter(self):
        return len(self.people_with_filter_ids)

    @property
    def observed_rate_per_child(self):
        return (
            self.number_of_observed_events / self.number_of_people_with_filter
        )

    @property
    def percent_of_children_with_events(self):
        return (
            self.number_of_children_with_event
            / self.number_of_people_with_filter
        )

    @property
    def column_name(self):
        return self.people_filter.filter_name

    def to_dict(self):
        return {
            "number_of_observed_events": self.number_of_observed_events,
            "number_of_children_with_event": self.number_of_children_with_event,
            "observed_rate_per_child": self.observed_rate_per_child,
            "percent_of_children_with_events": self.percent_of_children_with_events,
            "column": self.column_name,
        }

    def count_variant(self, family_variant, family_allele):
        if not (
            set(family_allele.variant_in_members) & self.people_with_filter_ids
        ):
            return
        if not family_allele.effect:
            return
        # FIXME: Avoid conversion of effect types to set
        if not (set(family_allele.effect.types) & self.effect_types):
            return
        self.observed_variants_ids.add(family_variant.fvuid)
        self.observed_people_with_event.update(
            set(family_allele.variant_in_members) & self.people_with_filter_ids
        )

    def is_empty(self):
        return (
            self.number_of_observed_events == 0
            and self.number_of_children_with_event == 0
            and self.observed_rate_per_child == 0
            and self.percent_of_children_with_events == 0
        )


class EffectRow(object):
    def __init__(self, genotype_data, denovo_variants, effect, people_filters):
        self.genotype_data = genotype_data
        self.denovo_variants = denovo_variants
        self.people_filters = people_filters

        self.effect_type = effect
        self.row = self._build_row()

    def to_dict(self):
        return OrderedDict(
            [
                ("effect_type", self.effect_type),
                ("row", [r.to_dict() for r in self.row]),
            ]
        )

    def count_variant(self, family_variant, family_allele):
        for effect_cell in self.row:
            effect_cell.count_variant(family_variant, family_allele)

    def _build_row(self):
        return [
            EffectCell(
                self.genotype_data,
                self.denovo_variants,
                people_filter,
                self.effect_type,
            )
            for people_filter in self.people_filters
        ]

    def is_row_empty(self):
        return all([value.is_empty() for value in self.row])

    def get_empty(self):
        return [value.is_empty() for value in self.row]

    def remove_elements(self, indexes):
        for index in sorted(indexes, reverse=True):
            self.row.pop(index)


class DenovoReportTable(object):
    def __init__(
        self,
        genotype_data,
        denovo_variants,
        effect_groups,
        effect_types,
        filter_collection,
    ):
        self.genotype_data = genotype_data
        self.denovo_variants = denovo_variants
        self.families = self.genotype_data.families

        self.people_filters = []
        for people_filter in filter_collection.filters:
            people_with_filter = people_filter.filter(
                self.families.persons.values()
            )
            people_with_filter_ids = set(
                [p.person_id for p in people_with_filter]
            )
            if len(people_with_filter_ids) > 0:
                people_filter.people_with_filter_ids = people_with_filter_ids
                self.people_filters.append(people_filter)

        self.effects = effect_groups + effect_types

        self.group_name = filter_collection.name
        self.columns = [
            people_filter.filter_name for people_filter in self.people_filters
        ]

        self.effect_groups = effect_groups
        self.effect_types = effect_types

        self.rows = self._build_rows()

    def to_dict(self):
        return OrderedDict(
            [
                ("rows", [r.to_dict() for r in self.rows]),
                ("group_name", self.group_name),
                ("columns", self.columns),
                ("effect_groups", self.effect_groups),
                ("effect_types", self.effect_types),
            ]
        )

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

        return list(
            filter(
                lambda effect_row: not effect_row.is_row_empty(), effect_rows
            )
        )

    def _build_rows(self):

        effect_rows = [
            EffectRow(
                self.genotype_data,
                self.denovo_variants,
                effect,
                self.people_filters,
            )
            for effect in self.effects
        ]

        for fv in self.denovo_variants:
            for fa in fv.alt_alleles:
                for effect_row in effect_rows:
                    effect_row.count_variant(fv, fa)

        effect_rows_empty_columns = list(
            map(
                all,
                np.array(
                    [effect_row.get_empty() for effect_row in effect_rows]
                ).T,
            )
        )

        effect_rows_empty_columns_index = list(
            np.where(effect_rows_empty_columns)[0]
        )

        self._remove_empty_columns(effect_rows_empty_columns_index)

        for effect_row in effect_rows:
            effect_row.remove_elements(effect_rows_empty_columns_index)

        effect_rows = self._remove_empty_rows(effect_rows)

        return effect_rows

    def is_empty(self):
        return all([row.is_row_empty() for row in self.rows])


class DenovoReport(object):
    def __init__(
        self, genotype_data, effect_groups, effect_types, filter_objects
    ):
        self.genotype_data = genotype_data
        self.effect_groups = effect_groups
        self.effect_types = effect_types
        self.filter_objects = filter_objects

        start = time.time()
        denovo_variants = genotype_data.query_variants(
            limit=None, inheritance="denovo",
        )
        self.denovo_variants = list(denovo_variants)
        elapsed = time.time() - start
        print(f"DENOVO REPORTS denovo variants query " f"in {elapsed:.2f} sec")

        start = time.time()
        self.tables = self._build_tables()
        elapsed = time.time() - start
        print(f"DENOVO REPORTS build " f"in {elapsed:.2f} sec")

    def to_dict(self):
        return OrderedDict([("tables", [t.to_dict() for t in self.tables])])

    def _build_tables(self):
        if len(self.denovo_variants) == 0:
            return []

        denovo_report_tables = []
        for filter_object in self.filter_objects:
            denovo_report_table = DenovoReportTable(
                self.genotype_data,
                self.denovo_variants,
                deepcopy(self.effect_groups),
                deepcopy(self.effect_types),
                filter_object,
            )
            if not denovo_report_table.is_empty():
                denovo_report_tables.append(denovo_report_table)

        return denovo_report_tables

    def is_empty(self):
        return len(self.tables) == 0
