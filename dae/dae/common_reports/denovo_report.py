from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from copy import deepcopy
from typing import Any, Dict, List, cast

import numpy as np

from dae.effect_annotation.effect import EffectTypesMixin
from dae.person_sets import PersonSet, PersonSetCollection
from dae.studies.study import GenotypeData
from dae.variants.family_variant import FamilyAllele, FamilyVariant

logger = logging.getLogger(__name__)


# FIXME: Too many instance attributes
class EffectCell:  # pylint: disable=too-many-instance-attributes
    """Class representing a cell in the denovo report table."""

    def __init__(self, person_set: PersonSet, effect: str) -> None:
        assert len(person_set.persons) > 0
        self.person_set = person_set
        self.effect = effect
        expanded_effect_types = \
            EffectTypesMixin().get_effect_types(effectTypes=effect)
        self.effect_types = set()
        if expanded_effect_types is not None:
            self.effect_types = set(expanded_effect_types)

        self.observed_variants_ids: set[str] = set()
        self.observed_people_with_event: set[str] = set([])
        self.person_set_persons = set(self.person_set.persons.keys())

        self.person_set_children = {
            p.person_id for p in self.person_set.get_children()
        }
        if len(self.person_set_children) == 0:
            self.person_set_children = set(self.person_set.persons.keys())

        logger.info(
            "DENOVO REPORTS: persons set %s children %s",
            self.person_set,
            len(self.person_set_children),
        )

    @property
    def number_of_observed_events(self) -> int:
        return len(self.observed_variants_ids)

    @property
    def number_of_children_with_event(self) -> int:
        return len(self.observed_people_with_event)

    @property
    def observed_rate_per_child(self) -> int | float:
        if self.number_of_observed_events == 0:
            return 0
        return self.number_of_observed_events / len(self.person_set_children)

    @property
    def percent_of_children_with_events(self) -> int | float:
        if self.number_of_children_with_event == 0:
            return 0
        return self.number_of_children_with_event / len(
            self.person_set_children,
        )

    @property
    def column_name(self) -> str:
        return f"{self.person_set.name} ({len(self.person_set_children)})"

    def to_dict(self) -> Dict[str, int | float | str]:
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

    def count_variant(
        self, family_variant: FamilyVariant,
        family_allele: FamilyAllele,
    ) -> None:
        """Count given variant in the cell data."""
        if not set(family_allele.variant_in_members) & \
                self.person_set_children:
            variant_in_members = set(family_allele.variant_in_members) & \
                self.person_set_persons
            if variant_in_members:
                logger.warning(
                    "denovo variant not in child: %s; %s; "
                    "person set: %s; "
                    "mismatched persons: %s",
                    family_allele,
                    family_allele.variant_in_members,
                    self.person_set.id,
                    variant_in_members,
                )
            return
        if not family_allele.effects:
            return
        # FIXME: Avoid conversion of effect types to set
        if not set(family_allele.effects.types) & self.effect_types:
            return
        self.observed_variants_ids.add(family_variant.fvuid)
        self.observed_people_with_event.update(
            set(family_allele.variant_in_members) & self.person_set_children)

    def is_empty(self) -> bool:
        return (
            self.number_of_observed_events == 0
            and self.number_of_children_with_event == 0
            and self.observed_rate_per_child == 0
            and self.percent_of_children_with_events == 0
        )


class EffectRow:
    """Class representing a row in the denovo report table."""

    def __init__(self, effect: str, person_sets: List[PersonSet]) -> None:
        self.person_sets = person_sets

        self.effect_type = effect
        self.row = self._build_row()

    def to_dict(self) -> dict[str, Any]:
        return {
            "effect_type": self.effect_type,
            "row": [r.to_dict() for r in self.row],
        }

    def _build_row(self) -> List[EffectCell]:
        return [
            EffectCell(
                person_set,
                self.effect_type,
            )
            for person_set in self.person_sets
        ]

    def count_variant(self, fv: FamilyVariant) -> None:
        for cell in self.row:
            for aa in fv.alt_alleles:
                fa = cast(FamilyAllele, aa)
                cell.count_variant(fv, fa)

    def is_row_empty(self) -> bool:
        return all(value.is_empty() for value in self.row)

    def get_empty(self) -> List[bool]:
        return [value.is_empty() for value in self.row]

    def remove_elements(self, indexes: list[int]) -> None:
        for index in sorted(indexes, reverse=True):
            cell = self.row[index]
            assert cell.is_empty()

            self.row.pop(index)


class DenovoReportTable:
    """Class representing a denovo report table JSON."""

    def __init__(
        self, json: dict[str, Any],
    ) -> None:
        self.rows = json["rows"]
        self.group_name = json["group_name"]
        self.columns = json["columns"]
        self.effect_groups = json["effect_groups"]
        self.effect_types = json["effect_types"]

    # FIXME: Too many locals
    @staticmethod
    def from_variants(  # pylint: disable=too-many-locals
        denovo_variants: Iterable[FamilyVariant],
        effect_groups: list[str],
        effect_types: list[str],
        person_set_collection: PersonSetCollection,
    ) -> DenovoReportTable:
        """Construct a denovo report table from variants."""
        person_sets = []
        for person_set in person_set_collection.person_sets.values():
            if len(person_set.persons) > 0:
                person_sets.append(person_set)

        effect_groups = list(effect_groups)
        effect_types = list(effect_types)
        effects = effect_groups + effect_types

        effect_rows = [
            EffectRow(
                effect,
                person_sets,
            )
            for effect in effects
        ]

        for fv in denovo_variants:
            for effect_row in effect_rows:
                effect_row.count_variant(fv)

        effect_rows_empty_columns = list(
            map(
                all,
                np.array(
                    [effect_row.get_empty() for effect_row in effect_rows],
                ).T,
            ),
        )

        effect_rows_empty_columns_index = list(
            np.where(effect_rows_empty_columns)[0],
        )

        for index in sorted(effect_rows_empty_columns_index, reverse=True):
            person_sets.pop(index)

        for effect_row in effect_rows:
            effect_row.remove_elements(effect_rows_empty_columns_index)
            if effect_row.is_row_empty():
                try:
                    effect_groups.remove(effect_row.effect_type)
                except ValueError:
                    pass
                try:
                    effect_types.remove(effect_row.effect_type)
                except ValueError:
                    pass
        effect_rows = list(filter(
            lambda effect_row: not effect_row.is_row_empty(), effect_rows,
        ))

        rows = effect_rows

        column_children = {}
        for row in rows:
            assert len(row.row) == len(person_sets)
            for cell in row.row:
                person_set_children = cell.person_set_children
                person_set_id = cell.person_set.id
                if person_set_id not in column_children:
                    column_children[person_set_id] = len(person_set_children)
                else:
                    count = column_children[person_set_id]
                    assert count == len(person_set_children)
        columns = []
        for person_set in person_sets:
            columns.append(
                f"{person_set.name} ({column_children[person_set.id]})")

        return DenovoReportTable({
            "rows": [r.to_dict() for r in rows],
            "group_name": person_set_collection.name,
            "columns": columns,
            "effect_groups": effect_groups,
            "effect_types": effect_types,
        })

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "group_name": self.group_name,
            "columns": self.columns,
            "effect_groups": self.effect_groups,
            "effect_types": self.effect_types,
        }

    def is_empty(self) -> bool:
        """Return whether the table does not have a single counted variant."""
        def _is_row_empty(row: dict[str, Any]) -> bool:
            for cell in row["row"]:
                if cell["number_of_observed_events"] > 0 \
                        or cell["number_of_children_with_event"] > 0 \
                        or cell["observed_rate_per_child"] > 0 \
                        or cell["percent_of_children_with_events"] > 0:
                    return False
            return True
        return all(_is_row_empty(row) for row in self.rows)


class DenovoReport:
    """Class representing a denovo report JSON."""

    def __init__(self, json: dict[str, Any]) -> None:
        self.tables = []
        if json is not None:
            self.tables = [DenovoReportTable(d) for d in json["tables"]]

    @staticmethod
    def from_genotype_study(
        genotype_data: GenotypeData,
        person_set_collections: List[PersonSetCollection],
    ) -> DenovoReport:
        """Create a denovo report JSON from a genotype data study."""
        config = genotype_data.config.common_report
        effect_groups = config.effect_groups
        effect_types = config.effect_types
        logger.info(
            "DENOVO REPORTS: person set collections %s",
            person_set_collections)
        start = time.time()

        denovo_report_tables = []
        if genotype_data.config.has_denovo:
            for psc in person_set_collections:
                denovo_variants = genotype_data.query_variants(
                    limit=None, inheritance=["denovo"],
                )
                denovo_report_table = DenovoReportTable.from_variants(
                    denovo_variants,
                    deepcopy(effect_groups),
                    deepcopy(effect_types),
                    psc,
                )
                if not denovo_report_table.is_empty():
                    denovo_report_tables.append(denovo_report_table)

        elapsed = time.time() - start
        logger.info(
            "DENOVO REPORTS build in %.2f sec", elapsed,
        )

        return DenovoReport({
            "tables": [t.to_dict() for t in denovo_report_tables],
        })

    def to_dict(self) -> dict[str, Any]:
        return {"tables": [t.to_dict() for t in self.tables]}

    def is_empty(self) -> bool:
        return len(self.tables) == 0
