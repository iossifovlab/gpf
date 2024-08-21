import copy
import enum
from collections import Counter
from typing import Any, cast

import duckdb
import numpy as np
from box import Box

from dae.pheno.common import InferenceConfig, MeasureType
from dae.pheno.utils.commons import remove_annoying_characters


class ClassifierReport:
    """Class used to collect clissifier reports."""

    MAX_CHARS = 32
    DISTRIBUTION_CUTOFF = 20

    def __init__(self) -> None:
        self.instrument_name: str | None = None
        self.measure_name: str | None = None
        self.measure_type: str | None = None
        self.count_total: int | None = None
        self.count_with_values: int | None = None
        self.count_without_values: int | None = None
        self.count_with_numeric_values: int | None = None
        self.count_with_non_numeric_values: int | None = None
        self.count_unique_values: int | None = None
        self.count_unique_numeric_values: int | None = None

        self.value_max_len: int | None = None

        self.unique_values: list[Any] | None = None
        self.numeric_values: list[int] | np.ndarray | None = None
        self.distribution: Any = None

    def set_measure(self, measure: Box) -> "ClassifierReport":
        self.instrument_name = measure.instrument_name
        self.measure_name = measure.measure_name
        self.measure_type = measure.measure_type.name
        return self

    @staticmethod
    def short_attributes() -> list[str]:
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

    def __repr__(self) -> str:
        return self.log_line(short=True)

    def log_line(self, *, short: bool = False) -> str:
        """Construct a log line in clissifier report."""
        attributes = self.short_attributes()
        values = [str(getattr(self, attr)).strip() for attr in attributes]
        values = [v.replace("\n", " ") for v in values]
        if not short:
            distribution = self.distribution
            assert distribution is not None
            distribution = [f"{v}\t{c}" for (v, c) in distribution]
            values.extend(distribution)
        return "\t".join(values)

    @staticmethod
    def short_header_line() -> str:
        attributes = ClassifierReport.short_attributes()
        return "\t".join(attributes)

    @staticmethod
    def header_line(*, short: bool = False) -> str:
        """Construct clissifier report header line."""
        attributes = ClassifierReport.short_attributes()
        if not short:
            distribution = [
                f"v{i}\tc{i}"
                for i in range(1, ClassifierReport.DISTRIBUTION_CUTOFF + 1)
            ]
            attributes.extend(distribution)
        return "\t".join(attributes)

    def calc_distribution_report(
        self, cursor: duckdb.DuckDBPyConnection | None = None,
        instrument_table_name: str | None = None,
    ) -> list[Any]:
        """Construct measure distribution report."""
        if self.distribution:
            return copy.deepcopy(self.distribution)
        assert cursor is not None
        assert instrument_table_name is not None

        measure_col = self.measure_name
        rows = cursor.sql(
            f'SELECT "{measure_col}", COUNT(*) as count '
            f"FROM {instrument_table_name} WHERE "
            f'"{measure_col}" IS NOT NULL '
            f'GROUP BY "{measure_col}" '
            f'ORDER BY count, "{measure_col}"',
        ).fetchall()
        counts: Counter = Counter()

        for row in rows:
            counts[str(row[0])] = row[1]

        distribution = list(counts.items())
        distribution = sorted(
            distribution, key=lambda _val_count: -_val_count[1],
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


def is_nan(val: Any) -> bool:
    """Check if the passed value is a NaN."""
    if val is None:
        return True
    if isinstance(val, str) and val.strip() == "":
        return True

    return type(val) in {float, np.float64, np.float32} and np.isnan(val)


class Convertible(enum.Enum):
    # pylint: disable=invalid-name
    nan = 0
    numeric = 1
    non_numeric = 2


def is_convertible_to_numeric(val: Any) -> Convertible:
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
    except ValueError:
        pass
    else:
        return Convertible.numeric

    return Convertible.non_numeric


def convert_to_numeric(val: Any) -> float | np.float_:
    """Convert passed value to float."""
    if is_convertible_to_numeric(val) == Convertible.numeric:
        return float(val)
    return np.nan


def convert_to_string(val: Any) -> str | None:
    """Convert passed value to string."""
    if is_nan(val):
        return None

    if isinstance(val, str):
        return str(remove_annoying_characters(val))

    return str(val)


class MeasureClassifier:
    """Defines a measure classification report."""

    def __init__(self, config: InferenceConfig):
        self.config = config

    @staticmethod
    def _meta_measures_numeric(
        cursor: duckdb.DuckDBPyConnection,
        table_name: str, measure_name: str,
        column_type: str, report: ClassifierReport,
    ) -> ClassifierReport:
        """Collect measure classification report for numeric values."""
        result = cursor.sql(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        assert result is not None
        total = cast(int, result[0])

        if column_type in ["FLOAT", "DOUBLE"]:
            result = cursor.sql(
                f'SELECT COUNT("{measure_name}") FROM {table_name} WHERE '
                f'"{measure_name}" != \'NaN\' AND '
                f'"{measure_name}" IS NOT NULL',
            ).fetchone()
            assert result is not None
            real_count = result[0]
        else:
            result = cursor.sql(
                f'SELECT COUNT("{measure_name}") FROM {table_name} WHERE '
                f'"{measure_name}" IS NOT NULL',
            ).fetchone()
            assert result is not None
            real_count = result[0]

        report.count_with_values = cast(int, real_count)
        report.count_with_numeric_values = cast(int, real_count)
        report.count_with_non_numeric_values = 0
        report.count_without_values = total - report.count_with_values

        if column_type in ["FLOAT", "DOUBLE"]:
            result = cursor.sql(
                f'SELECT COUNT(DISTINCT "{measure_name}") '
                f"FROM {table_name} WHERE "
                f'"{measure_name}" != \'NaN\' AND '
                f'"{measure_name}" IS NOT NULL',
            ).fetchone()
            assert result is not None
            unique_count = result[0]
        else:
            result = cursor.sql(
                f'SELECT COUNT(DISTINCT "{measure_name}") '
                f"FROM {table_name} WHERE "
                f'"{measure_name}" IS NOT NULL',
            ).fetchone()
            assert result is not None
            unique_count = result[0]

        report.count_unique_values = unique_count
        report.count_unique_numeric_values = unique_count

        rows = cursor.sql(
            f'SELECT DISTINCT "{measure_name}" FROM {table_name} WHERE '
            f'"{measure_name}" IS NOT NULL',
        ).fetchall()
        unique_values = [row[0] for row in rows]
        report.unique_values = unique_values

        rows = cursor.sql(
            f'SELECT "{measure_name}" FROM {table_name} WHERE '
            f'"{measure_name}" IS NOT NULL',
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
        report: ClassifierReport,
    ) -> ClassifierReport:
        """Collect measure classification report for text values."""
        report.count_with_values = 0

        result = cursor.sql(
            "SELECT COUNT(*) FROM ("
            f'SELECT "{measure_name}", '
            f'TRY_CAST("{measure_name}" AS FLOAT) as casted '
            f"from {table_name} "
            f'WHERE "{measure_name}" IS NULL OR casted = \'nan\''
            ")",
        ).fetchone()
        assert result is not None
        report.count_without_values = result[0]

        result = cursor.sql(
            "SELECT COUNT(casted) FROM ("
            f'SELECT TRY_CAST("{measure_name}" AS FLOAT) as casted '
            f"from {table_name} WHERE casted IS NOT NULL AND casted != 'nan'"
            ")",
        ).fetchone()
        assert result is not None
        report.count_with_numeric_values = result[0]
        report.count_with_values += result[0]

        result = cursor.sql(
            f'SELECT COUNT("{measure_name}") FROM ('
            f'SELECT "{measure_name}", '
            f'TRY_CAST("{measure_name}" AS FLOAT) as casted '
            f"from {table_name} WHERE casted IS NULL AND "
            f'"{measure_name}" IS NOT NULL'
            ")",
        ).fetchone()
        assert result is not None
        report.count_with_non_numeric_values = result[0]
        report.count_with_values += result[0]

        rows = list(cursor.sql(
            f'SELECT DISTINCT "{measure_name}" FROM ('
            f'SELECT "{measure_name}", '
            f'TRY_CAST("{measure_name}" AS FLOAT) as casted '
            f'from {table_name} WHERE "{measure_name}" IS NOT NULL'
            ")",
        ).fetchall())
        assert rows is not None
        report.unique_values = [row[0] for row in rows]
        report.count_unique_values = len(report.unique_values)

        rows = cursor.sql(
            f"SELECT casted FROM ("
            f'SELECT "{measure_name}", '
            f'TRY_CAST("{measure_name}" AS FLOAT) as casted '
            f"from {table_name} WHERE casted IS NOT NULL AND casted != 'nan'"
            ")",
        ).fetchall()
        report.numeric_values = np.array([row[0] for row in rows])
        report.count_unique_numeric_values = len(
            np.unique(report.numeric_values),
        )

        assert (
            report.count_total
            == cast(int, report.count_with_values)
            + cast(int, report.count_without_values)
        )
        assert (
            report.count_with_values
            == cast(int, report.count_with_numeric_values)
            + cast(int, report.count_with_non_numeric_values)
        )

        return report

    @staticmethod
    def meta_measures(
            cursor: duckdb.DuckDBPyConnection,
            table_name: str, measure_name: str,
            report: ClassifierReport | None = None,
    ) -> ClassifierReport:
        """Build classifier meta report."""
        if report is None:
            report = ClassifierReport()

        result = cursor.sql(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        assert result is not None

        report.count_total = result[0]

        result = cursor.sql(
            f'SELECT COUNT("{measure_name}") FROM {table_name}',
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
                f"Could not find column {measure_name} in {table_name}",
            )

        if column_type in {
            "TINYINT",
            "SMALLINT",
            "INTEGER",
            "BIGINT",
            "HUGEINT",
            "FLOAT",
            "DOUBLE",
            "BOOLEAN",
        }:
            return MeasureClassifier._meta_measures_numeric(
                cursor, table_name, measure_name, column_type, report,
            )

        if column_type in ["VARCHAR", "DATE", "TIMESTAMP"]:
            return MeasureClassifier._meta_measures_text(
                cursor, table_name, measure_name, report,
            )

        raise ValueError(f"NOT SUPPORTED VALUES TYPES {column_type}")

    @staticmethod
    def convert_to_numeric(values: np.ndarray) -> np.ndarray:
        """Convert value to numeric."""
        if values.dtype in {
            int,
            float,
            float,
            int,
            np.dtype("int64"),
            np.dtype("float64"),
        }:
            return values

        result = np.array([convert_to_numeric(val) for val in values])
        assert len(result) == len(values)
        assert result.dtype == np.float64

        return result

    @staticmethod
    def convert_to_string(values: np.ndarray) -> np.ndarray:
        if len(values) == 0:
            return np.array([])
        return np.array([convert_to_string(val) for val in values])

    def classify(self, rep: ClassifierReport) -> MeasureType:
        """Classify a measure based on classification report."""
        conf = self.config

        if (
            conf.min_individuals is not None and
            rep.count_with_values is not None and 
            rep.count_with_values < conf.min_individuals
        ):
            return MeasureType.raw

        non_numeric = (
            1.0 * cast(int, rep.count_with_non_numeric_values)
        ) / cast(int, rep.count_with_values)

        if non_numeric <= conf.non_numeric_cutoff:
            if (
                rep.count_unique_numeric_values is not None and
                conf.continuous.min_rank is not None and
                rep.count_unique_numeric_values >= conf.continuous.min_rank
            ):
                return MeasureType.continuous
            if (
                rep.count_unique_numeric_values is not None and
                conf.ordinal.min_rank is not None and
                rep.count_unique_numeric_values >= conf.ordinal.min_rank
            ):
                return MeasureType.ordinal

            return MeasureType.raw

        if (
            rep.count_unique_values is not None
            and conf.categorical.min_rank is not None
            and conf.categorical.max_rank is not None
            and rep.count_unique_values >= conf.categorical.min_rank
            and rep.count_unique_values <= conf.categorical.max_rank
            # and rep.value_max_len <= conf.value_max_len
        ):
            return MeasureType.categorical

        return MeasureType.raw
