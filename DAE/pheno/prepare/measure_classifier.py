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

        # self.rank = None
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
        result = np.array([convert_to_string(val) for val in values])
        return result

    @staticmethod
    def should_convert_to_numeric(classifier, cutoff=0.06):
        if classifier.count_with_values == 0:
            return False

        non_numeric = (1.0 * classifier.count_with_non_numeric_values) / \
            classifier.count_with_values

        if non_numeric <= cutoff:
            return True

        return False

    def check_continuous_rank(self, rank, individuals):
        if rank < self.config.classification.continuous.min_rank:
            return False
        if individuals < self.config.classification.min_individuals:
            return False
        return True

    def check_ordinal_rank(self, rank, individuals):
        if rank < self.config.classification.ordinal.min_rank:
            return False
        if individuals < self.config.classification.min_individuals:
            return False
        return True

    def check_categorical_rank(self, rank, individuals):
        if rank < self.config.classification.categorical.min_rank:
            return False
        if individuals < self.config.classification.min_individuals:
            return False
        return True

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

#     def text_classifier(self, classifier_report, measure, series):
#         values = series.values
#         values = self.convert_to_string(values)
#         unique_values = np.unique(values)
#         unique_values = np.array([v for v in unique_values if v is not None])
#
#         rank = len(unique_values)
#         individuals = classifier_report.count_with_values
#         classifier_report.rank = rank
#         classifier_report.unique_values = unique_values
#         classifier_report.values = values
#
#         if rank == 0 or \
#                 individuals < self.config.classification.min_individuals:
#             measure.measure_type = MeasureType.skipped
#             measure.individuals = individuals
#             return measure
#
#         if not self.check_categorical_rank(rank, individuals):
#             measure.measure_type = MeasureType.other
#             measure.individuals = individuals
#             return measure
#
#         max_len = max(map(len, unique_values))
#         if max_len > 32:
#             measure.measure_type = MeasureType.text
#         elif rank > individuals / 3.0:
#             measure.measure_type = MeasureType.text
#         else:
#             measure.measure_type = MeasureType.categorical
#
#         measure.individuals = individuals
#         return measure
#
#
#     def numeric_classifier(self, classifier_report, measure, series):
#         values = series.values
#         if not self.should_convert_to_numeric(classifier_report):
#             return None
#
#         values = self.convert_to_numeric(values)
#         unique_values = np.unique(np.array([
#             filter(lambda v: not np.isnan(v), values)
#         ]))
#
#         rank = len(unique_values)
#         individuals = classifier_report.count_with_values
#         classifier_report.rank = rank
#         classifier_report.unique_values = unique_values
#         classifier_report.values = values
#
#         if rank == 0 or \
#                 individuals < self.config.classification.min_individuals:
#             measure.measure_type = MeasureType.skipped
#             measure.individuals = individuals
#             return measure
#
#         if self.check_continuous_rank(rank, individuals):
#             measure.measure_type = MeasureType.continuous
#             measure.individuals = individuals
#             return measure
#         elif self.check_ordinal_rank(rank, individuals):
#             measure.measure_type = MeasureType.continuous
#             measure.individuals = individuals
#             return measure
#
#         return None
