import numpy as np
from dae.pheno.common import MeasureType


class PhenoFilter(object):
    def __init__(self, phenotype_data, measure_id):
        assert phenotype_data.has_measure(measure_id)

        self.phenotype_data = phenotype_data
        self.measure_id = measure_id


class PhenoFilterSet(PhenoFilter):
    def __init__(self, phenotype_data, measure_id, values_set):
        super(PhenoFilterSet, self).__init__(phenotype_data, measure_id)

        measure_type = phenotype_data.get_measure(measure_id).measure_type
        assert measure_type == MeasureType.categorical

        assert type(values_set) in (list, set, tuple)
        self.value_set = values_set

    def apply(self, df):
        return df[df[self.measure_id].isin(self.value_set)]


class PhenoFilterRange(PhenoFilter):
    def __init__(self, phenotype_data, measure_id, values_range):
        super(PhenoFilterRange, self).__init__(phenotype_data, measure_id)
        measure_type = phenotype_data.get_measure(measure_id).measure_type
        assert measure_type == MeasureType.continuous or \
            measure_type == MeasureType.ordinal
        assert isinstance(values_range, list) or \
            isinstance(values_range, tuple) or \
            isinstance(values_range, set), \
            f"{values_range} ({type(values_range)})"

        if len(values_range) == 2:
            assert isinstance(values_range, list) or isinstance(
                values_range, tuple
            )
            assert len(values_range) == 2
            self.values_min, self.values_max = values_range
        else:
            assert len(values_range) == 1
            for value in values_range:
                self.values_max = self.values_min = value

    def apply(self, df):
        if self.values_min is not None and self.values_max is not None:
            return df[
                np.logical_and(
                    df[self.measure_id] >= self.values_min,
                    df[self.measure_id] <= self.values_max,
                )
            ]
        elif self.values_min is not None:
            return df[df[self.measure_id] >= self.values_min]
        elif self.values_max is not None:
            return df[df[self.measure_id] <= self.values_max]
        else:
            return df[-np.isnan(df[self.measure_id])]


class PhenoFilterBuilder(object):
    def __init__(self, phenotype_data):
        self.phenotype_data = phenotype_data

    def make_filter(self, measure_id, constraints):
        measure = self.phenotype_data.get_measure(measure_id)
        assert measure is not None
        if measure.measure_type == MeasureType.categorical:
            return PhenoFilterSet(self.phenotype_data, measure_id, constraints)
        else:
            return PhenoFilterRange(
                self.phenotype_data, measure_id, constraints
            )


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
