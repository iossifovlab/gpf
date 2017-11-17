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


class Convertable(enum.Enum):
    nan = 0
    numeric = 1
    non_numeric = 2


def is_convertible_to_numeric(val):
    if val is None:
        return Convertable.nan
    if isinstance(val, str):
        val = val.strip()
        if val.strip() == '':
            return Convertable.nan
    if isinstance(val, float):
        if np.isnan(val):
            return Convertable.nan

    try:
        val = float(val)
        return Convertable.numeric
    except ValueError:
        pass

    return Convertable.non_numeric


class MeasureClassifier(object):

    def __init__(self, measure, df):
        self.measure = measure
        self.df = df

    @staticmethod
    def numeric_classifier(values):
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
                if convertable == Convertable.nan:
                    r.count_without_values = len(vals)
                elif convertable == Convertable.numeric:
                    r.count_with_values += len(vals)
                    r.count_with_numeric_values = len(vals)
                else:
                    assert convertable == Convertable.non_numeric
                    r.count_with_values += len(vals)
                    r.count_with_non_numeric_values = len(vals)
            return r

        print("OOOPS!!!!")
