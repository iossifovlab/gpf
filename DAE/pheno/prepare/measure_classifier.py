'''
Created on Nov 16, 2017

@author: lubo
'''
import numpy as np
import pandas as pd
import itertools
import enum
from pheno.common import MeasureType
from pheno.utils.commons import remove_annoying_characters


class ClassifierReport(object):

    def __init__(self):
        self.instrument_name = None
        self.measure_name = None
        self.count_with_values = None
        self.count_without_values = None
        self.count_with_numeric_values = None
        self.count_with_non_numeric_values = None
        self.count_unique_values = None
        self.count_total = None

        self.value_max_len = None
        self.unique_values = None
        self.numeric_values = None
        self.string_values = None
        self.distribution = None

    def __repr__(self):
        return "ClassifierReport(total: {}; " \
            "with values: {}; "\
            "with numeric values: {}; " \
            "with non-numeric values: {}; "\
            "without values: {}; " \
            "unique values: {})".format(
                self.count_total,
                self.count_with_values,
                self.count_with_numeric_values,
                self.count_with_non_numeric_values,
                self.count_without_values,
                self.count_unique_values,
            )

    def log_line(self):
        return '\t'.join(map(str, [
            self.count_total,
            self.count_with_values,
            self.count_with_numeric_values,
            self.count_with_non_numeric_values,
            self.count_without_values,
            self.count_unique_values,
            self.value_max_len,
        ]))


def is_nan(val):
    if val is None:
        return True
    if isinstance(val, str):
        if val.strip() == '':
            return True
    if type(val) in set([float, np.float64, np.float32]) and np.isnan(val):
        return True
    return False


class Convertible(enum.Enum):
    nan = 0
    numeric = 1
    non_numeric = 2


def is_convertible_to_numeric(val):
    if val is None:
        return Convertible.nan
    if isinstance(val, str):
        val = val.strip()
        if val == '':
            return Convertible.nan
    if isinstance(val, float) and np.isnan(val):
        return Convertible.nan

    if isinstance(val, bool):
        return Convertible.non_numeric
    if isinstance(val, np.bool_):
        return Convertible.non_numeric

    try:
        val = float(val)
        return Convertible.numeric
    except ValueError:
        pass

    return Convertible.non_numeric


def convert_to_numeric(val):
    if is_convertible_to_numeric(val) == Convertible.numeric:
        return float(val)
    return np.nan


def convert_to_string(val):
    if is_nan(val):
        return None

    if type(val) in set([str, unicode]) or \
            isinstance(val, str) or isinstance(val, unicode):
        return unicode(remove_annoying_characters(val).decode('utf-8'))
    else:
        return unicode(val)


class MeasureClassifier(object):

    def __init__(self, config):
        self.config = config

    @staticmethod
    def meta_measures_numeric(values, report):
        total = len(values)
        values = MeasureClassifier.convert_to_numeric(values)
        real_values = np.array([v for v in values if not is_nan(v)])
        unique_values = np.unique(real_values)
        report.count_with_values = len(real_values)
        report.count_with_numeric_values = len(real_values)
        report.count_with_non_numeric_values = 0
        report.count_without_values += total - report.count_with_values
        report.count_unique_values = len(unique_values)
        report.unique_values = unique_values
        report.numeric_values = values
        report.string_values = MeasureClassifier.convert_to_string(real_values)
        if len(report.string_values) == 0:
            report.value_max_len = 0
        else:
            report.value_max_len = max(map(len, report.string_values))

        assert report.count_total == \
            report.count_with_values + report.count_without_values
        assert report.count_with_values == \
            report.count_with_numeric_values + \
            report.count_with_non_numeric_values
        return report

    @staticmethod
    def meta_measures_text(values, report):
        grouped = itertools.groupby(values,
                                    is_convertible_to_numeric)
        report.count_with_values = 0
        report.count_with_numeric_values = 0
        report.count_with_non_numeric_values = 0
        for convertable, vals in grouped:
            vals = list(vals)

            if convertable == Convertible.nan:
                report.count_without_values += len(vals)
            elif convertable == Convertible.numeric:
                report.count_with_values += len(vals)
                report.count_with_numeric_values += len(vals)
            else:
                assert convertable == Convertible.non_numeric
                report.count_with_values += len(vals)
                report.count_with_non_numeric_values += len(vals)

        report.string_values = np.array([
            v for v in MeasureClassifier.convert_to_string(values)
            if v is not None])
        report.unique_values = np.unique(report.string_values)
        report.count_unique_values = len(report.unique_values)
        report.value_max_len = max(map(len, report.string_values))
        assert report.count_total == \
            report.count_with_values + report.count_without_values
        assert report.count_with_values == \
            report.count_with_numeric_values + \
            report.count_with_non_numeric_values
        return report

    @staticmethod
    def meta_measures(series, report=None):
        assert isinstance(series, pd.Series)

        if report is None:
            report = ClassifierReport()

        report.count_total = len(series)
        values = series.values
        report.count_without_values = report.count_total - len(values)

        if values.dtype in set([int, float, np.float, np.int,
                                np.dtype('int64'), np.dtype('float64')]):
            return MeasureClassifier.meta_measures_numeric(values, report)

        if values.dtype == np.object or values.dtype.char == 'S' or \
                values.dtype == bool:
            return MeasureClassifier.meta_measures_text(values, report)

        assert False, "NOT SUPPORTED VALUES TYPES"

    @staticmethod
    def convert_to_numeric(values):
        if values.dtype in set([int, float, np.float, np.int,
                                np.dtype('int64'), np.dtype('float64')]):
            return values

        result = np.array([convert_to_numeric(val) for val in values])
        assert len(result) == len(values)
        assert result.dtype == np.float64

        return result

    @staticmethod
    def convert_to_string(values):
        if len(values) == 0:
            return np.array([])
        return np.array([convert_to_string(val) for val in values])

    def classify(self, report):
        config = self.config.classification
        if report.count_with_values < config.min_individuals:
            return MeasureType.skipped
        non_numeric = (1.0 * report.count_with_non_numeric_values) / \
            report.count_with_values

        if non_numeric <= config.non_numeric_cutoff:
            # numeric measure
            if report.count_unique_values >= config.continuous.min_rank:
                return MeasureType.continuous
            if report.count_unique_values >= config.ordinal.min_rank:
                return MeasureType.ordinal
            if report.count_unique_values >= config.categorical.min_rank:
                return MeasureType.categorical
            return MeasureType.other
        else:
            # text measure
            if report.value_max_len > config.value_max_len:
                return MeasureType.text
            if report.count_unique_values > report.count_with_values / 3.0:
                return MeasureType.text
            if report.count_unique_values >= config.categorical.min_rank:
                return MeasureType.categorical
            return MeasureType.other
