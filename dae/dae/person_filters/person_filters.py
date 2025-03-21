from collections.abc import Collection
from typing import Any

import numpy as np
import pandas as pd

from dae.pedigrees.families_data import FamiliesData
from dae.pheno.common import MeasureType
from dae.pheno.pheno_data import Measure, PhenotypeData


class PersonFilter:
    """Generic interface for a filter working on FamiliesData objects."""

    def apply_to_df(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def apply(
        self, families: FamiliesData, roles: list[str] | None = None,
    ) -> set[str]:
        raise NotImplementedError


class CriteriaFilter(PersonFilter):  # pylint: disable=abstract-method
    """Filter individuals based on given criteria and their values."""

    def __init__(self, criteria: str, values: Collection):
        self.criteria: str = criteria
        self.values: Collection = values

    def apply(
        self, families: FamiliesData, roles: list[str] | None = None,
    ) -> set[str]:
        """Return a set of person ids for individuals matching the filter."""
        ped_df = families.ped_df.copy()
        if roles is not None:
            ped_df = ped_df.loc[ped_df["role"].astype(str).isin(roles)]
        ped_df[self.criteria] = ped_df[self.criteria].astype(str)
        ped_df = self.apply_to_df(ped_df)
        return set(ped_df["person_id"])


class PersonFilterSet(CriteriaFilter):
    """Filter based on a specific set of values."""

    def apply_to_df(self, df: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(self.values, (list, set, tuple)):
            raise TypeError(f"{self.values} ({type(self.values)})")
        return df[df[self.criteria].isin(self.values)]


class PersonFilterRange(CriteriaFilter):
    """Filter based on a range of values."""

    def __init__(self, criteria: str, values: Collection):
        super().__init__(criteria, values)
        if isinstance(self.values, (list, tuple)):
            self.values_min, self.values_max, *_ = self.values
        elif isinstance(self.values, set) and len(self.values) == 1:
            self.values_min = self.values_max = next(iter(self.values))
        else:
            raise TypeError(f"{self.values} ({type(self.values)})")

    def apply_to_df(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.values_min is not None and self.values_max is not None:
            return df[  # type: ignore
                np.logical_and(
                    df[self.criteria] >= self.values_min,
                    df[self.criteria] <= self.values_max,
                )
            ]
        if self.values_min is not None:
            return df[df[self.criteria] >= self.values_min]  # type: ignore
        if self.values_max is not None:
            return df[df[self.criteria] <= self.values_max]  # type: ignore
        return df[df[self.criteria].notna()]


class PhenoFilter(CriteriaFilter):  # pylint: disable=abstract-method
    """Filter using a phenotype measure as criteria."""

    def __init__(
        self, criteria: str, values: Collection, phenotype_data: PhenotypeData,
    ):
        super().__init__(criteria, values)
        self.measure_df = self.apply_to_df(
            phenotype_data.get_people_measure_values_df([self.criteria]),
        )

    def apply(
        self, families: FamiliesData, roles: list[str] | None = None,
    ) -> set[str]:
        ids = set()
        for person_id in self.measure_df["person_id"]:
            if person_id not in families.persons_by_person_id:
                continue
            if roles is not None:
                persons = families.persons_by_person_id[person_id]
                if not any(str(p.role) in roles for p in persons):
                    continue
            ids.add(person_id)
        return ids


class PhenoFilterSet(PhenoFilter, PersonFilterSet):
    """Filter based on a specific set of phenotype measure values."""

    def __init__(
        self,
        measure: Measure,
        values: Collection,
        phenotype_data: PhenotypeData,
    ):
        assert measure.measure_type in (
            MeasureType.categorical, MeasureType.ordinal,
        )
        self.measure: Measure = measure
        super().__init__(self.measure.measure_id, values, phenotype_data)


class PhenoFilterRange(PhenoFilter, PersonFilterRange):
    """Filter based on a range of phenotype measure values."""

    def __init__(
        self,
        measure: Measure,
        values: Collection,
        phenotype_data: PhenotypeData,
    ):
        assert measure.measure_type in (
            MeasureType.continuous, MeasureType.ordinal,
        )
        self.measure: Measure = measure
        super().__init__(self.measure.measure_id, values, phenotype_data)


class FamilyFilter(PersonFilter):
    """Apply a given PersonFilter, but collect a set of family ids instead."""

    def __init__(self, person_filter: PersonFilter):
        self.person_filter = person_filter

    def apply_to_df(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.person_filter.apply_to_df(df)

    def apply(
        self, families: FamiliesData,
        *args: Any, **kwargs: Any,
    ) -> set[str]:
        return families.families_of_persons(
            self.person_filter.apply(families, *args, **kwargs),
        )


def make_pedigree_filter(pedigree_filter: dict) -> PersonFilter:
    """Create a PersonFilter based on a dict config."""
    result_filter = PersonFilterSet(
        pedigree_filter["source"],
        set(pedigree_filter["selection"]["selection"]),
    )
    if pedigree_filter.get("role"):
        return FamilyFilter(result_filter)
    return result_filter


def make_pheno_filter(
    pheno_filter: dict, phenotype_data: PhenotypeData,
) -> PersonFilter:
    """Create a PhenoFilter based on a dict config."""
    measure = phenotype_data.get_measure(pheno_filter["source"])
    pheno_filter_type = MeasureType.from_str(pheno_filter["sourceType"])
    selection = pheno_filter["selection"]

    result_filter: PhenoFilter
    if pheno_filter_type == MeasureType.categorical:
        result_filter = PhenoFilterSet(
            measure, set(selection["selection"]), phenotype_data,
        )
    else:
        result_filter = PhenoFilterRange(
            measure, (selection["min"], selection["max"]), phenotype_data,
        )

    if pheno_filter.get("role"):
        return FamilyFilter(result_filter)
    return result_filter


def make_pheno_filter_beta(
    pheno_filter: dict, phenotype_data: PhenotypeData,
) -> PersonFilter:
    """Create a PhenoFilter based on a dict config."""
    measure = phenotype_data.get_measure(pheno_filter["source"])
    pheno_filter_type = MeasureType.from_str(pheno_filter["histogramType"])

    result_filter: PhenoFilter
    if pheno_filter_type == MeasureType.categorical:
        result_filter = PhenoFilterSet(
            measure, set(pheno_filter["values"]), phenotype_data,
        )
    else:
        result_filter = PhenoFilterRange(
            measure, (pheno_filter["min"], pheno_filter["max"]), phenotype_data,
        )

    if pheno_filter["isFamily"] is True:
        return FamilyFilter(result_filter)
    return result_filter
