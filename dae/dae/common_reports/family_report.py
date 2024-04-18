"""Provides family report class."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from dae.common_reports.family_counter import FamiliesGroupCounters
from dae.pedigrees.families_data import FamiliesData
from dae.person_sets import PersonSetCollection
from dae.studies.study import GenotypeData


class FamiliesReport:
    """Class representing a family report JSON."""

    def __init__(self, json: dict[str, Any]):
        families_counters = [
            FamiliesGroupCounters(fc) for fc in json  # type: ignore
        ]
        self.families_counters = {
            fc.group_name: fc for fc in families_counters
        }

    @staticmethod
    def from_genotype_study(
        genotype_data_study: GenotypeData,
        person_set_collections: Iterable[PersonSetCollection],
    ) -> FamiliesReport:
        """Create a family report from a genotype study."""
        config = genotype_data_study.config.common_report
        return FamiliesReport.from_families_data(
            genotype_data_study.families, person_set_collections,
            config.draw_all_families)

    @staticmethod
    def from_families_data(
        families: FamiliesData,
        person_set_collections: Iterable[PersonSetCollection],
        draw_all_families: bool = True,
    ) -> FamiliesReport:
        """Create a family report from families data."""
        families_counters = [
            FamiliesGroupCounters.from_families(
                families,
                person_set_collection,
                draw_all_families,
            )
            for person_set_collection in person_set_collections
        ]
        return FamiliesReport([  # type: ignore
            fc.to_dict(full=True) for fc in families_counters
        ])

    def to_dict(self, full: bool = False) -> list[dict[str, Any]]:
        return [
            fc.to_dict(full=full) for fc in self.families_counters.values()
        ]
