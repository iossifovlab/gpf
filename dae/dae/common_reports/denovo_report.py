import time
import logging
import numpy as np
from copy import deepcopy

from dae.utils.effect_utils import EffectTypesMixin


logger = logging.getLogger(__name__)


class EffectCell:
    def __init__(self, denovo_variants, person_set, effect):
        self.denovo_variants = denovo_variants
        assert len(person_set.persons) > 0
        self.person_set = person_set
        self.effect = effect
        self.effect_types = set(
            EffectTypesMixin().get_effect_types(effectTypes=effect)
        )

        self.observed_variants_ids = set()
        self.observed_people_with_event = set([])
        self.person_set_persons = set(self.person_set.persons.keys())

        self.person_set_children = {
            p.person_id for p in self.person_set.get_children()
        }
        if len(self.person_set_children) == 0:
            self.person_set_children = set(self.person_set.persons.keys())

        for fv in self.denovo_variants:
            for fa in fv.alt_alleles:
                self.count_variant(fv, fa)

        logger.info(
            f"DENOVO REPORTS: persons set {self.person_set} children "
            f"{len(self.person_set_children)}")

    @property
    def number_of_observed_events(self):
        return len(self.observed_variants_ids)

    @property
    def number_of_children_with_event(self):
        return len(self.observed_people_with_event)

    @property
    def observed_rate_per_child(self):
        if self.number_of_observed_events == 0:
            return 0
        return self.number_of_observed_events / len(self.person_set_children)

    @property
    def percent_of_children_with_events(self):
        if self.number_of_children_with_event == 0:
            return 0
        return self.number_of_children_with_event / len(
            self.person_set_children
        )

    @property
    def column_name(self):
        return f"{self.person_set.name} ({len(self.person_set_children)})"

    def to_dict(self):
        return {
            "number_of_observed_events":
            self.number_of_observed_events,
            "number_of_children_with_event":
            self.number_of_children_with_event,
            "observed_rate_per_child":
            self.observed_rate_per_child,
            "percent_of_children_with_events":
            self.percent_of_children_with_events,
            "column":
            self.column_name,
        }

    def count_variant(self, family_variant, family_allele):
        if not set(family_allele.variant_in_members) & \
                self.person_set_children:
            variant_in_members = set(family_allele.variant_in_members) & \
                self.person_set_persons
            if variant_in_members:
                logger.warning(
                    f"denovo variant not in child: {family_allele}; "
                    f"{family_allele.variant_in_members}; "
                    f"person set: {self.person_set.id}; "
                    f"mismatched persons: {variant_in_members}")
            return
        if not family_allele.effects:
            print("No effect")
            return
        # FIXME: Avoid conversion of effect types to set
        if not (set(family_allele.effects.types) & self.effect_types):
            return
        self.observed_variants_ids.add(family_variant.fvuid)
        self.observed_people_with_event.update(
            set(family_allele.variant_in_members) & self.person_set_children)

    def is_empty(self):
        return (
            self.number_of_observed_events == 0
            and self.number_of_children_with_event == 0
            and self.observed_rate_per_child == 0
            and self.percent_of_children_with_events == 0
        )


class EffectRow(object):
    def __init__(self, denovo_variants, effect, person_sets):
        self.denovo_variants = denovo_variants
        self.person_sets = person_sets

        self.effect_type = effect
        self.row = self._build_row()

    def to_dict(self):
        return {
            "effect_type": self.effect_type,
            "row": [r.to_dict() for r in self.row],
        }

    def _build_row(self):
        return [
            EffectCell(
                self.denovo_variants,
                person_set,
                self.effect_type,
            )
            for person_set in self.person_sets
        ]

    def is_row_empty(self):
        return all([value.is_empty() for value in self.row])

    def get_empty(self):
        return [value.is_empty() for value in self.row]

    def remove_elements(self, indexes):
        for index in sorted(indexes, reverse=True):
            cell = self.row[index]
            assert cell.is_empty()

            self.row.pop(index)


class DenovoReportTable(object):
    def __init__(
            self,
            denovo_variants,
            effect_groups,
            effect_types,
            person_set_collection):

        self.denovo_variants = denovo_variants

        self.person_set_collection = person_set_collection
        self.person_sets = []
        for person_set in person_set_collection.person_sets.values():
            if len(person_set.persons) > 0:
                self.person_sets.append(person_set)

        self.effect_groups = list(effect_groups)
        self.effect_types = list(effect_types)
        self.effects = effect_groups + effect_types

        self.rows = self._build_rows()
        self._build_column_titles()

    def _build_column_titles(self):
        column_children = {}
        for row in self.rows:
            assert len(row.row) == len(self.person_sets)
            for cell in row.row:
                person_set_children = cell.person_set_children
                person_set_id = cell.person_set.id
                if person_set_id not in column_children:
                    column_children[person_set_id] = len(person_set_children)
                else:
                    count = column_children[person_set_id]
                    assert count == len(person_set_children)
        self.columns = []
        for person_set in self.person_sets:
            self.columns.append(
                f"{person_set.name} ({column_children[person_set.id]})")

    def to_dict(self):
        return {
            "rows": [r.to_dict() for r in self.rows],
            "group_name": self.person_set_collection.name,
            "columns": self.columns,
            "effect_groups": self.effect_groups,
            "effect_types": self.effect_types,
        }

    def _remove_empty_columns(self, indexes):
        for index in sorted(indexes, reverse=True):
            self.person_sets.pop(index)

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
                self.denovo_variants,
                effect,
                self.person_sets,
            )
            for effect in self.effects
        ]

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
            self,
            genotype_data,
            effect_groups,
            effect_types,
            person_set_collections):

        self.genotype_data = genotype_data
        self.effect_groups = effect_groups
        self.effect_types = effect_types
        self.person_set_collections = person_set_collections
        print(
            f"DENOVO REPORTS: person set collections {person_set_collections}")
        start = time.time()
        denovo_variants = genotype_data.query_variants(
            limit=None, inheritance=["denovo"],
        )
        self.denovo_variants = list(denovo_variants)
        elapsed = time.time() - start
        logger.info(
            f"DENOVO REPORTS: denovo variants query in {elapsed:.2f} sec")
        logger.info(
            f"DENOVO REPORTS: denovo variants count is "
            f"{len(self.denovo_variants)}")

        start = time.time()
        self.tables = self._build_tables()
        elapsed = time.time() - start
        logger.info(f"DENOVO REPORTS build " f"in {elapsed:.2f} sec")

    def to_dict(self):
        return {"tables": [t.to_dict() for t in self.tables]}

    def _build_tables(self):
        if len(self.denovo_variants) == 0:
            return []

        denovo_report_tables = []
        for person_set_collection in self.person_set_collections:
            denovo_report_table = DenovoReportTable(
                self.denovo_variants,
                deepcopy(self.effect_groups),
                deepcopy(self.effect_types),
                person_set_collection,
            )
            if not denovo_report_table.is_empty():
                denovo_report_tables.append(denovo_report_table)

        return denovo_report_tables

    def is_empty(self):
        return len(self.tables) == 0
