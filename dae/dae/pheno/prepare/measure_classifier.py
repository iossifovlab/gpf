"""
Created on Nov 16, 2017

@author: lubo
"""
import numpy as np
import pandas as pd
import itertools
import enum
from dae.pheno.common import MeasureType
from dae.pheno.utils.commons import remove_annoying_characters
from collections import Counter
import copy


class ClassifierReport(object):

    MAX_CHARS = 32
    DISTRIBUTION_CUTOFF = 20

    def __init__(self):
        self.instrument_name = None
        self.measure_name = None
        self.measure_type = None
        self.count_total = None
        self.count_with_values = None
        self.count_without_values = None
        self.count_with_numeric_values = None
        self.count_with_non_numeric_values = None
        self.count_unique_values = None
        self.count_unique_numeric_values = None

        self.value_max_len = None

        self.unique_values = None
        self.numeric_values = None
        self.string_values = None
        self.distribution = None

    def set_measure(self, measure):
        self.instrument_name = measure.instrument_name
        self.measure_name = measure.measure_name
        self.measure_type = measure.measure_type.name
        return self

    @staticmethod
    def short_attributes():
        return [
            "instrument_name",
            "measure_name",
            "measure_type",
            "count_total",
            "count_with_values",
            "count_with_numeric_values",
            "count_with_non_numeric_values",
            "count_without_values",
            "count_unique_values",
            "count_unique_numeric_values",
            "value_max_len",
        ]

    def __repr__(self):
        return self.log_line()

    def log_line(self, short=False):
        attributes = self.short_attributes()
        values = [str(getattr(self, attr)).strip() for attr in attributes]
        values = [v.replace("\n", " ") for v in values]
        if not short:
            distribution = self.calc_distribution_report()
            distribution = ["{}\t{}".format(v, c) for (v, c) in distribution]
            values.extend(distribution)
        return "\t".join(values)

    @staticmethod
    def short_header_line():
        attributes = ClassifierReport.short_attributes()
        return "\t".join(attributes)

    @staticmethod
    def header_line(short=False):
        attributes = ClassifierReport.short_attributes()
        if not short:
            distribution = [
                "v{}\tc{}".format(i, i)
                for i in range(1, ClassifierReport.DISTRIBUTION_CUTOFF + 1)
            ]
            attributes.extend(distribution)
        return "\t".join(attributes)

    def calc_distribution_report(self):
        if self.distribution:
            return copy.deepcopy(self.distribution)

        assert self.string_values is not None
        counts = Counter()
        for val in self.string_values:
            counts[val] += 1
        distribution = [(val, count) for (val, count) in list(counts.items())]
        distribution = sorted(
            distribution, key=lambda _val_count: -_val_count[1]
        )
        distribution = distribution[: self.DISTRIBUTION_CUTOFF]
        distribution = [
            (val[: self.MAX_CHARS], count) for (val, count) in distribution
        ]
        if len(distribution) < self.DISTRIBUTION_CUTOFF:
            ext = [
                (" ", " ")
                for _i in range(self.DISTRIBUTION_CUTOFF - len(distribution))
            ]
            distribution.extend(ext)
        self.distribution = distribution
        return copy.deepcopy(self.distribution)


def is_nan(val):
    if val is None:
        return True
    if isinstance(val, str):
        if val.strip() == "":
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
        if val == "":
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

    if (
        type(val) in set([str, str])
        or isinstance(val, str)
        or isinstance(val, str)
    ):
        return str(remove_annoying_characters(val))
    else:
        return str(val)


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
        report.count_unique_numeric_values = len(unique_values)

        report.unique_values = unique_values
        report.numeric_values = real_values
        report.string_values = MeasureClassifier.convert_to_string(real_values)
        if len(report.string_values) == 0:
            report.value_max_len = 0
        else:
            report.value_max_len = max(list(map(len, report.string_values)))

        assert (
            report.count_total
            == report.count_with_values + report.count_without_values
        )
        assert (
            report.count_with_values
            == report.count_with_numeric_values
            + report.count_with_non_numeric_values
        )
        return report

    @staticmethod
    def meta_measures_text(values, report):
        grouped = itertools.groupby(values, is_convertible_to_numeric)
        report.count_with_values = 0
        report.count_with_numeric_values = 0
        report.count_with_non_numeric_values = 0
        numeric_values = []
        for convertable, vals in grouped:
            vals = list(vals)

            if convertable == Convertible.nan:
                report.count_without_values += len(vals)
            elif convertable == Convertible.numeric:
                report.count_with_values += len(vals)
                report.count_with_numeric_values += len(vals)
                numeric_values.extend(vals)
            else:
                assert convertable == Convertible.non_numeric
                report.count_with_values += len(vals)
                report.count_with_non_numeric_values += len(vals)

        report.string_values = np.array(
            [
                v
                for v in MeasureClassifier.convert_to_string(values)
                if v is not None
            ]
        )
        report.unique_values = np.unique(report.string_values)
        report.count_unique_values = len(report.unique_values)
        report.numeric_values = MeasureClassifier.convert_to_numeric(
            np.array(numeric_values)
        )
        report.count_unique_numeric_values = len(
            np.unique(report.numeric_values)
        )
        if len(report.string_values) == 0:
            report.value_max_len = 0
        else:
            report.value_max_len = max(list(map(len, report.string_values)))
        assert (
            report.count_total
            == report.count_with_values + report.count_without_values
        )
        assert (
            report.count_with_values
            == report.count_with_numeric_values
            + report.count_with_non_numeric_values
        )
        return report

    @staticmethod
    def meta_measures(series, report=None):
        assert isinstance(series, pd.Series)

        if report is None:
            report = ClassifierReport()

        report.count_total = len(series)
        values = series.values
        report.count_without_values = report.count_total - len(values)

        if values.dtype in set(
            [
                int,
                float,
                float,
                int,
                np.dtype("int64"),
                np.dtype("float64"),
            ]
        ):
            return MeasureClassifier.meta_measures_numeric(values, report)

        if (
            values.dtype == np.object
            or values.dtype.char == "S"
            or values.dtype == bool
        ):
            return MeasureClassifier.meta_measures_text(values, report)

        assert False, "NOT SUPPORTED VALUES TYPES"

    @staticmethod
    def convert_to_numeric(values):
        if values.dtype in set(
            [
                int,
                float,
                float,
                int,
                np.dtype("int64"),
                np.dtype("float64"),
            ]
        ):
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

    def classify(self, rep):
        conf = self.config.classification

        if rep.count_with_values < conf.min_individuals:
            return MeasureType.raw

        non_numeric = (
            1.0 * rep.count_with_non_numeric_values
        ) / rep.count_with_values

        if non_numeric <= conf.non_numeric_cutoff:
            if rep.count_unique_numeric_values >= conf.continuous.min_rank:
                return MeasureType.continuous

            if rep.count_unique_numeric_values >= conf.ordinal.min_rank:
                return MeasureType.ordinal

            return MeasureType.raw
        else:
            if (
                rep.count_unique_values >= conf.categorical.min_rank
                and rep.count_unique_values <= conf.categorical.max_rank
                # and rep.value_max_len <= conf.value_max_len
            ):
                return MeasureType.categorical

            return MeasureType.raw


#     def classify(self, report):
#         config = self.config.classification
#         if report.count_with_values < config.min_individuals:
#             return MeasureType.skipped
#         non_numeric = (1.0 * report.count_with_non_numeric_values) / \
#             report.count_with_values
#
#         if non_numeric <= config.non_numeric_cutoff:
#             # numeric measure
#             if report.count_unique_values >= config.continuous.min_rank:
#                 return MeasureType.continuous
#             if report.count_unique_values >= config.ordinal.min_rank:
#                 return MeasureType.ordinal
#             if report.count_unique_values >= config.categorical.min_rank:
#                 return MeasureType.categorical
#             return MeasureType.other
#         else:
#             # text measure
#             if report.value_max_len > config.value_max_len:
#                 return MeasureType.text
#             if report.count_unique_values > report.count_with_values / 3.0:
#                 return MeasureType.text
#             if report.count_unique_values >= config.categorical.min_rank:
#                 return MeasureType.categorical
#             return MeasureType.other


# type definition graph? correlation phenoTool
# MeasureType.skipped <explicitly requested in config> NA NA NA
# MeasureType.continuous more than a 'few' numeric possible Y Y Y
# MeasureType.ordinal one or a 'few' numeric possible Y Y (but one v)
#                                                           Y (but one v)
# MeasureType.categorical one or a 'few' non-numeric possible Y F N
# MeasureType.raw everything else N N N
#
# In the future we may fish out these from the 'raw'
# MeasureType.text free text N N N
# MeasureType.id id column N N N

# The default configuration
#     {
#      'classification': {
#      'min_individuals': 1,
#      'non_numeric_cutoff': 0.06,
#      'value_max_len': 32,
#      'continuous': {
#      'min_rank': 15
#      },
#      'ordinal': {
#      'min_rank': 1
#      },
#      'categorical': {
#      'min_rank': 1,
#      'max_rank': 15
#      }
#     }
# Report fields
#     report.count_with_values
#     report.count_with_non_numeric_values (## NEW)
#     report.count_unique_values
#     report.count_unique_numeric_values
#     report.value_max_len
