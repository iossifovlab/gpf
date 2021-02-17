import numpy as np
import pandas as pd
from typing import Set, List, Optional
from collections.abc import Collection
from dae.pedigrees.family import FamiliesData
from dae.pheno.common import MeasureType
from dae.pheno.pheno_db import Measure, PhenotypeData


class PersonFilter():
    def __init__(self, criteria: str, values: Collection):
        self.criteria: str = criteria
        self.values: str = values

    def _apply_to_df(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError()

    def apply(
        self, families: FamiliesData, roles: Optional[List[str]] = None
    ) -> Set[str]:
        ped_df = families.ped_df.copy()
        if roles is not None:
            ped_df = ped_df.loc[ped_df["role"].astype(str).isin(roles)]
        ped_df[self.criteria] = ped_df[self.criteria].astype(str)
        ped_df = self._apply_to_df(ped_df)
        return set(ped_df["person_id"])


class PersonFilterSet(PersonFilter):
    def __init__(self, criteria: str, values: Collection):
        super(PersonFilterSet, self).__init__(criteria, values)
        assert type(values) in (list, set, tuple)

    def _apply_to_df(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df[self.criteria].isin(self.values)]


class PersonFilterRange(PersonFilter):
    def __init__(self, criteria: str, values: Collection):
        super(PersonFilterRange, self).__init__(criteria, values)
        assert isinstance(values, list) or \
            isinstance(values, tuple) or \
            isinstance(values, set), \
            f"{values} ({type(values)})"
        if len(values) == 2:
            assert isinstance(values, list) or isinstance(values, tuple)
            self.values_min, self.values_max = values
        else:
            assert len(values) == 1
            self.values_min = self.values_max = list(values)[0]

    def _apply_to_df(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.values_min is not None and self.values_max is not None:
            return df[
                np.logical_and(
                    df[self.criteria] >= self.values_min,
                    df[self.criteria] <= self.values_max,
                )
            ]
        elif self.values_min is not None:
            return df[df[self.criteria] >= self.values_min]
        elif self.values_max is not None:
            return df[df[self.criteria] <= self.values_max]
        else:
            return df[-np.isnan(df[self.criteria])]


class PhenoFilter(PersonFilter):
    def apply(
        self,
        families: FamiliesData,
        phenotype_data: PhenotypeData,
        roles: Optional[List[str]] = None
    ) -> Set[str]:
        measure_df = self._apply_to_df(
            phenotype_data.get_measure_values_df(self.criteria)
        )
        ids = set()
        for person_id in measure_df["person_id"]:
            if person_id not in families.persons:
                continue
            if roles is not None:
                if str(families.persons[person_id].role) not in roles:
                    continue
            ids.add(person_id)
        return ids


class PhenoFilterSet(PhenoFilter, PersonFilterSet):
    def __init__(self, measure: Measure, values: Collection):
        super(PhenoFilterSet, self).__init__(measure.measure_id, values)
        self.measure: Measure = measure
        assert measure.measure_type in (
            MeasureType.categorical,  MeasureType.ordinal)


class PhenoFilterRange(PhenoFilter, PersonFilterRange):
    def __init__(self, measure: Measure, values: Collection):
        super(PhenoFilterRange, self).__init__(measure.measure_id, values)
        self.measure: Measure = measure
        assert measure.measure_type in (
            MeasureType.continuous, MeasureType.ordinal
        )


class FamilyFilter(PersonFilter):
    def __init__(self, person_filter: PersonFilter):
        self.person_filter = person_filter

    def _apply_to_df(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.person_filter._apply_to_df(df)

    def apply(self, *args, **kwargs) -> List[str]:
        families = args[0]
        return families.families_of_persons(
            self.person_filter.apply(*args, **kwargs)
        )


def make_pedigree_filter(pedigree_filter: dict) -> PersonFilter:
    result_filter = PersonFilterSet(
        pedigree_filter["source"],
        set(pedigree_filter["selection"]["selection"])
    )
    if pedigree_filter.get("role"):
        result_filter = FamilyFilter(result_filter)
    return result_filter


def make_pheno_filter(
    pheno_filter: dict, phenotype_data: PhenotypeData
) -> PersonFilter:
    measure = phenotype_data.get_measure(pheno_filter["source"])

    pheno_filter_type = MeasureType.from_str(
        pheno_filter["sourceType"])

    selection = pheno_filter["selection"]
    if pheno_filter_type in (MeasureType.continuous, MeasureType.ordinal):
        constraints = tuple([selection["min"], selection["max"]])
    else:
        constraints = set(selection["selection"])

    if pheno_filter_type == MeasureType.categorical:
        result_filter = PhenoFilterSet(measure, constraints)
    else:
        result_filter = PhenoFilterRange(measure, constraints)

    if pheno_filter.get("role"):
        result_filter = FamilyFilter(result_filter)

    return result_filter
