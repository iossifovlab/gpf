'''
Created on Nov 16, 2017

@author: lubo
'''
import numpy as np
import itertools
import enum


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


class MeasureClassifier(object):

    def __init__(self, measure, df):
        self.measure = measure
        self.df = df

    @staticmethod
    def numeric_classifier(values):
        assert isinstance(values, np.ndarray)

        r = ClassifierReport()

        print(values.dtype)

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
                    r.count_with_numeric_values = len(vals)
                else:
                    assert convertable == Convertible.non_numeric
                    r.count_with_values += len(vals)
                    r.count_with_non_numeric_values = len(vals)
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
        result = np.array([str(val) for val in values])
        return result

    @staticmethod
    def should_convert_to_numeric(values, cutoff=0.03):
        classifier = MeasureClassifier.numeric_classifier(values)
        non_numeric = (1.0 * classifier.count_with_non_numeric_values) / \
            classifier.count_with_values

        if non_numeric <= cutoff:
            return True

        return False
