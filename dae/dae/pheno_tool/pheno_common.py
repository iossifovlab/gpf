import numpy as np
import pandas as pd
from collections.abc import Collection
from dae.pheno.common import MeasureType
from dae.pheno.pheno_db import Measure


class PersonFilter():
    def __init__(self, criteria: str, values: Collection):
        self.criteria: str = criteria
        self.values: str = values
        assert type(values) in (list, set, tuple)


class PersonFilterSet(PersonFilter):
    def __init__(self, criteria: str, values: Collection):
        super(PersonFilterSet, self).__init__(criteria, values)

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df[self.criteria].isin(self.values)]


class PersonFilterRange(PersonFilter):
    def __init__(self, criteria: str, values: Collection):
        super(PersonFilterRange, self).__init__(criteria, values)
        if len(values) == 2:
            self.values_min, self.values_max = values
        else:
            self.values_min = self.values_max = values[0]

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
        super(PersonFilterSet, self).__init__(measure.name, values)
        self.measure: Measure = measure
        assert measure.measure_type == MeasureType.categorical


class PhenoFilterRange(PersonFilterRange):
    def __init__(self, measure: Measure, values: Collection):
        super(PersonFilterRange, self).__init__(measure.name, values)
        self.measure: Measure = measure
        assert measure.measure_type in (
            MeasureType.continuous, MeasureType.ordinal
        )


class PhenoFilterBuilder(object):
    def __init__(self, phenotype_data):
        self.phenotype_data = phenotype_data

    def make_filter(self, pheno_filter: dict) -> PersonFilter:
        measure = self.phenotype_data.get_measure(pheno_filter["source"])
        measure_type = measure.measure_type
        selection = pheno_filter["selection"]
        if measure_type in (MeasureType.continuous, MeasureType.ordinal):
            constraints = tuple([selection["min"], selection["max"]])
        else:
            constraints = set(selection["selection"])
        if measure_type == MeasureType.categorical:
            return PersonFilterSet(measure, constraints)
        else:
            return PersonFilterRange(measure, constraints)


class PhenoResult(object):
    def __init__(self):
        self.pvalue = np.nan
        self.positive_count = np.nan
        self.positive_mean = np.nan
        self.positive_deviation = np.nan
        self.negative_count = np.nan
        self.negative_mean = np.nan
        self.negative_deviation = np.nan

    def _set_positive_stats(self, p_count, p_mean, p_std):
        self.positive_count = p_count
        self.positive_mean = p_mean
        self.positive_deviation = p_std

    def _set_negative_stats(self, n_count, n_mean, n_std):
        self.negative_count = n_count
        self.negative_mean = n_mean
        self.negative_deviation = n_std

    def __repr__(self):
        return "PhenoResult: pvalue={}; pos={} (neg={})".format(
            self.pvalue, self.positive_count, self.negative_count
        )
