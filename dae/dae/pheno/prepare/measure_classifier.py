import itertools
import enum
import copy
import duckdb
from collections import Counter
from typing import Optional, List
from numbers import Number

import numpy as np
import pandas as pd

from dae.pheno.common import MeasureType
from dae.pheno.utils.commons import remove_annoying_characters


class ClassifierReport:
    """Class used to collect clissifier reports."""

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
        self.string_values: Optional[np.ndarray] = None
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
        return "temp"#self.log_line()

    def log_line(self, short=False):
        """Construct a log line in clissifier report."""
        attributes = self.short_attributes()
        values = [str(getattr(self, attr)).strip() for attr in attributes]
        values = [v.replace("\n", " ") for v in values]
        if not short:
            distribution = self.calc_distribution_report()
            distribution = [f"{v}\t{c}" for (v, c) in distribution]
            values.extend(distribution)
        return "\t".join(values)

    @staticmethod
    def short_header_line():
        attributes = ClassifierReport.short_attributes()
        return "\t".join(attributes)

    @staticmethod
    def header_line(short=False):
        """Construct clissifier report header line."""
        attributes = ClassifierReport.short_attributes()
        if not short:
            distribution = [
                f"v{i}\tc{i}"
                for i in range(1, ClassifierReport.DISTRIBUTION_CUTOFF + 1)
            ]
            attributes.extend(distribution)
        return "\t".join(attributes)

    def calc_distribution_report(self):
        """Construct measure distribution report."""
        if self.distribution:
            return copy.deepcopy(self.distribution)
        counts: Counter = Counter()

        assert self.string_values is not None
        for val in self.string_values:  # pylint: disable=not-an-iterable
            counts[val] += 1
        distribution = list(counts.items())
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
            distribution.extend(ext)  # type: ignore
        self.distribution = distribution
        return copy.deepcopy(self.distribution)


def is_nan(val):
    """Check if the passed value is a NaN."""
    if val is None:
        return True
    if isinstance(val, str):
        if val.strip() == "":
            return True
    if type(val) in set([float, np.float64, np.float32]) and np.isnan(val):
        return True
    return False


class Convertible(enum.Enum):
    # pylint: disable=invalid-name
    nan = 0
    numeric = 1
    non_numeric = 2


def is_convertible_to_numeric(val):
    """Check if the passed string is convertible to number."""
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
    """Convert passed value to float."""
    if is_convertible_to_numeric(val) == Convertible.numeric:
        return float(val)
    return np.nan


def convert_to_string(val):
    """Convert passed value to string."""
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


class MeasureClassifier:
    """Defines a measure classification report."""

    def __init__(self, config):
        self.config = config

    @staticmethod
    def _meta_measures_numeric(
        cursor: duckdb.DuckDBPyConnection,
        table_name: str, measure_name: str,
        column_type: str, report: ClassifierReport
    ):
        """Collect measure classification report for numeric values."""
        result = cursor.sql(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        assert result is not None
        total = result[0]

        if column_type in ["FLOAT", "DOUBLE"]:
            result = cursor.sql(
                f"SELECT COUNT({measure_name}) FROM {table_name} WHERE "
                f"{measure_name} != 'NaN' AND "
                f"{measure_name} IS NOT NULL"
            ).fetchone()
            assert result is not None
            real_count = result[0]
        else:
            result = cursor.sql(
                f"SELECT COUNT({measure_name}) FROM {table_name} WHERE "
                f"{measure_name} IS NOT NULL"
            ).fetchone()
            assert result is not None
            real_count = result[0]

        report.count_with_values = real_count
        report.count_with_numeric_values = real_count
        report.count_with_non_numeric_values = 0
        report.count_without_values = total - report.count_with_values

        if column_type in ["FLOAT", "DOUBLE"]:
            result = cursor.sql(
                f"SELECT COUNT(DISTINCT {measure_name}) "
                f"FROM {table_name} WHERE "
                f"{measure_name} != 'NaN' AND "
                f"{measure_name} IS NOT NULL"
            ).fetchone()
            assert result is not None
            unique_count = result[0]
        else:
            result = cursor.sql(
                f"SELECT COUNT(DISTINCT {measure_name}) "
                f"FROM {table_name} WHERE "
                f"{measure_name} IS NOT NULL"
            ).fetchone()
            assert result is not None
            unique_count = result[0]

        report.count_unique_values = unique_count
        report.count_unique_numeric_values = unique_count

        rows = cursor.sql(
            f"SELECT DISTINCT {measure_name} FROM {table_name} WHERE "
            f"{measure_name} IS NOT NULL"
        ).fetchall()
        unique_values = [row[0] for row in rows]
        report.unique_values = unique_values

        rows = cursor.sql(
            f"SELECT {measure_name} FROM {table_name} WHERE "
            f"{measure_name} IS NOT NULL"
        ).fetchall()
        real_values = [row[0] for row in rows]
        report.numeric_values = real_values

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
    def _meta_measures_text(
        cursor: duckdb.DuckDBPyConnection,
        table_name: str, measure_name: str,
        report: ClassifierReport
    ):
        """Collect measure classification report for text values."""
        report.count_with_values = 0

        result = cursor.sql(
            "SELECT COUNT(*) FROM ("
            f"SELECT {measure_name}, "
            f"TRY_CAST({measure_name} AS FLOAT) as casted "
            f"from {table_name} WHERE {measure_name} IS NULL OR casted = 'nan'"
            ")"
        ).fetchone()
        assert result is not None
        report.count_without_values = result[0]

        result = cursor.sql(
            "SELECT COUNT(casted) FROM ("
            f"SELECT TRY_CAST({measure_name} AS FLOAT) as casted "
            f"from {table_name} WHERE casted IS NOT NULL AND casted != 'nan'"
            ")"
        ).fetchone()
        assert result is not None
        report.count_with_numeric_values = result[0]
        report.count_with_values += result[0]

        result = cursor.sql(
            f"SELECT COUNT({measure_name}) FROM ("
            f"SELECT {measure_name}, "
            f"TRY_CAST({measure_name} AS FLOAT) as casted "
            f"from {table_name} WHERE casted IS NULL AND "
            f"{measure_name} IS NOT NULL"
            ")"
        ).fetchone()
        assert result is not None
        report.count_with_non_numeric_values = result[0]
        report.count_with_values += result[0]

        rows = list(cursor.sql(
            f"SELECT DISTINCT {measure_name} FROM ("
            f"SELECT {measure_name}, "
            f"TRY_CAST({measure_name} AS FLOAT) as casted "
            f"from {table_name} WHERE {measure_name} IS NOT NULL"
            ")"
        ).fetchall())
        assert rows is not None
        report.unique_values = [row[0] for row in rows]
        report.count_unique_values = len(report.unique_values)

        rows = cursor.sql(
            f"SELECT casted FROM ("
            f"SELECT {measure_name}, "
            f"TRY_CAST({measure_name} AS FLOAT) as casted "
            f"from {table_name} WHERE casted IS NOT NULL AND casted != 'nan'"
            ")"
        ).fetchall()
        report.numeric_values = np.array([row[0] for row in rows])
        report.count_unique_numeric_values = len(
            np.unique(report.numeric_values)
        )

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
    def meta_measures(cursor, table_name, measure_name, report=None):
        """Build classifier meta report."""

        if report is None:
            report = ClassifierReport()

        result = cursor.sql(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        assert result is not None

        report.count_total = result[0]

        result = cursor.sql(
            f"SELECT COUNT({measure_name}) FROM {table_name}"
        ).fetchone()
        assert result is not None

        report.count_without_values = report.count_total - result[0]

        rows = cursor.sql(f"DESCRIBE {table_name}")

        column_type = None
        for row in rows.fetchall():
            if row[0] == measure_name:
                column_type = row[1]
                break
        if column_type is None:
            raise ValueError(
                f"Could not find column {measure_name} in {table_name}"
            )

        if column_type in set(
            [
                "TINYINT",
                "SMALLINT",
                "INTEGER",
                "BIGINT",
                "HUGEINT",
                "FLOAT",
                "DOUBLE",
                "BOOLEAN"
            ]
        ):
            return MeasureClassifier._meta_measures_numeric(
                cursor, table_name, measure_name, column_type, report
            )

        if column_type == "VARCHAR":
            return MeasureClassifier._meta_measures_text(
                cursor, table_name, measure_name, report
            )

        assert False, f"NOT SUPPORTED VALUES TYPES {column_type}"

    @staticmethod
    def convert_to_numeric(values):
        """Convert value to numeric."""
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
    def convert_to_string(values) -> np.ndarray:
        if len(values) == 0:
            return np.array([])
        return np.array([convert_to_string(val) for val in values])

    def classify(self, rep):
        """Classify a measure based on classification report."""
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
