'''
Created on Nov 16, 2017

@author: lubo
'''
import numpy as np
import itertools
import enum
from pheno.common import MeasureType
from pheno.utils.commons import remove_annoying_characters


class ClassifierReport(object):

    def __init__(self):
        self.count_with_values = None
        self.count_without_values = None
        self.count_with_numeric_values = None
        self.count_with_non_numeric_values = None

        self.unique_values = None
        self.histogram = None

    def __repr__(self):
        return "ClassifierReport(with values: {}; "\
            "with numeric values: {}; " \
            "with non-numeric values: {}; "\
            "without values: {})".format(
                self.count_with_values,
                self.count_with_numeric_values,
                self.count_with_non_numeric_values,
                self.count_without_values
            )

    def log_line(self):
        return ','.join(map(str, [
            self.count_with_values,
            self.count_with_numeric_values,
            self.count_with_non_numeric_values,
            self.count_without_values
        ]))


def is_nan(val):
    if val is None:
        return True
    if isinstance(val, str):
        if val.strip() == '':
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
        if val.strip() == '':
            return Convertible.nan
    if isinstance(val, float):
        if np.isnan(val):
            return Convertible.nan

    if isinstance(val, bool):
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
    if type(val) in set([str, unicode]):
        return unicode(remove_annoying_characters(val))
    else:
        return unicode(val)


class MeasureClassifier(object):

    def __init__(self, config):
        self.config = config

    @staticmethod
    def classify(values):
        assert isinstance(values, np.ndarray)

        r = ClassifierReport()

        if values.dtype in set([int, float, np.float, np.int,
                                np.dtype('int64'), np.dtype('float64')]):
            r.count_with_values = len(values)
            r.count_with_numeric_values = len(values)
            r.count_with_non_numeric_values = 0
            r.count_without_values = 0

            return r

        if values.dtype == np.object or values.dtype.char == 'S':
            grouped = itertools.groupby(
                values,
                is_convertible_to_numeric
            )
            r.count_with_values = 0
            r.count_without_values = 0
            r.count_with_numeric_values = 0
            r.count_with_non_numeric_values = 0

            for convertable, vals in grouped:
                vals = list(vals)

                if convertable == Convertible.nan:
                    r.count_without_values = len(vals)
                elif convertable == Convertible.numeric:
                    r.count_with_values += len(vals)
                    r.count_with_numeric_values += len(vals)
                else:
                    assert convertable == Convertible.non_numeric
                    r.count_with_values += len(vals)
                    r.count_with_non_numeric_values += len(vals)
            return r

        if values.dtype == bool:
            r.count_with_values = len(values)
            r.count_with_numeric_values = 0
            r.count_with_non_numeric_values = len(values)
            r.count_without_values = 0

            return r

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

    def numeric_classifier(self, classifier_report, measure, values):
        if not self.should_convert_to_numeric(classifier_report):
            return None

        values = self.convert_to_numeric(values)
        unique_values = np.unique(values)

        rank = len(unique_values)
        individuals = classifier_report.count_with_values

        if self.check_continuous_rank(rank, individuals):
            measure.measure_type = MeasureType.continuous
            measure.individuals = individuals
            return measure
        elif self.check_ordinal_rank(rank, individuals):
            measure.measure_type = MeasureType.continuous
            measure.individuals = individuals
            return measure

        return None

    def text_classifier(self, classifier_report, measure, values):
        values = self.convert_to_string(values)
        unique_values = np.unique(values)
        rank = len(unique_values)
        individuals = classifier_report.count_with_values

        if not self.check_categorical_rank(rank, individuals):
            print("MEASURE: {}; rank: {}, individuals: {}".format(
                measure.measure_id, rank, individuals
            ))
            measure.measure_type = MeasureType.other
            measure.individuals = individuals
            return measure

        unique_values = np.array([v for v in unique_values if v is not None])
        max_len = max(map(len, unique_values))
        if max_len > 32:
            measure.measure_type = MeasureType.text
        elif rank > 0.5 * individuals:
            measure.measure_type = MeasureType.text
        else:
            measure.measure_type = MeasureType.categorical

        measure.individuals = individuals
        return measure
