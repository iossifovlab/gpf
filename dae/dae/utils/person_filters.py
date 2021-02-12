import numpy as np
import pandas as pd
from collections.abc import Collection
from dae.pheno.common import MeasureType
from dae.pheno.pheno_db import Measure


class PersonFilter():
    def __init__(self, criteria: str, values: Collection):
        self.criteria: str = criteria
        self.values: str = values


class PersonFilterSet(PersonFilter):
    def __init__(self, criteria: str, values: Collection):
        super(PersonFilterSet, self).__init__(criteria, values)
        assert type(values) in (list, set, tuple)

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
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

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
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


class PhenoFilterSet(PersonFilterSet):
    def __init__(self, measure: Measure, values: Collection):
        super(PhenoFilterSet, self).__init__(measure.measure_id, values)
        self.measure: Measure = measure
        assert measure.measure_type in (
            MeasureType.categorical,  MeasureType.ordinal)


class PhenoFilterRange(PersonFilterRange):
    def __init__(self, measure: Measure, values: Collection):
        super(PhenoFilterRange, self).__init__(measure.measure_id, values)
        self.measure: Measure = measure
        assert measure.measure_type in (
            MeasureType.continuous, MeasureType.ordinal
        )


class PhenoFilterBuilder(object):
    def __init__(self, phenotype_data):
        self.phenotype_data = phenotype_data

    def make_filter(self, pheno_filter: dict) -> PersonFilter:
        measure = self.phenotype_data.get_measure(pheno_filter["source"])
        print("pheno_filter:", pheno_filter)

        pheno_filter_type = MeasureType.from_str(
            pheno_filter["sourceType"])

        # measure_type = measure.measure_type
        selection = pheno_filter["selection"]
        if pheno_filter_type in (MeasureType.continuous, MeasureType.ordinal):
            constraints = tuple([selection["min"], selection["max"]])
        else:
            constraints = set(selection["selection"])
        if pheno_filter_type == MeasureType.categorical:
            return PhenoFilterSet(measure, constraints)
        else:
            return PhenoFilterRange(measure, constraints)