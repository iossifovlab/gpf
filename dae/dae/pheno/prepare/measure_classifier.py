import enum
from typing import Any, cast

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
        self.numeric_values: list[float | None] | np.ndarray | None = None
        self.distribution: Any = None

        self.min_value: int | None = None
        self.max_value: int | None = None
        self.values_domain: str | None = None
        self.rank: int | None = None
        self.db_name: str | None = None

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
        if not short:
            attributes.append("values_domain")
        values = [str(getattr(self, attr)).strip() for attr in attributes]
        values = [v.replace("\n", " ") for v in values]
        return "\t".join(values)


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


def classification_reference_impl(
    measure_values: list[str | None], config: InferenceConfig,
) -> tuple[list[Any], ClassifierReport]:
    """Reference implementation for measure classification."""
    report = ClassifierReport()
    unique_values: set[str] = set()
    numeric_values: list[float | None] = []
    unique_numeric_values = set()
    report.count_total = len(measure_values)
    numeric_count = 0
    measure_type = None
    none_count = 0

    if config.measure_type is not None:
        measure_type = MeasureType.from_str(config.measure_type)

    for val in measure_values:
        if val is None:
            none_count += 1
            numeric_values.append(None)
            continue
        unique_values.add(val)
        try:
            num_value = float(val)
            numeric_values.append(num_value)
            numeric_count += 1
            unique_numeric_values.add(num_value)
        except ValueError:
            numeric_values.append(None)

    report.numeric_values = numeric_values
    report.count_with_values = len(measure_values) - none_count
    report.count_without_values = none_count
    report.count_with_numeric_values = numeric_count
    report.count_with_non_numeric_values = \
        report.count_with_values - report.count_with_numeric_values
    report.unique_values = list(unique_values)
    report.count_unique_values = len(report.unique_values)
    report.count_unique_numeric_values = len(unique_numeric_values)

    assert (
        report.count_total
        == report.count_with_values
        + report.count_without_values
    )
    assert (
        report.count_with_values
        == report.count_with_numeric_values
        + report.count_with_non_numeric_values
    )
    classifier = MeasureClassifier(config)

    if measure_type is None:
        measure_type = classifier.classify(report)
    report.measure_type = measure_type

    non_null_numeric_values = list(
        filter(lambda x: x is not None, report.numeric_values))

    if measure_type in {MeasureType.continuous, MeasureType.ordinal}:
        if len(non_null_numeric_values) == 0:
            raise ValueError(
                "Measure is set as numeric but has no numeric values!",
            )
        report.min_value = np.min(cast(np.ndarray, non_null_numeric_values))
        if isinstance(report.min_value, np.bool_):
            report.min_value = np.int8(report.min_value)
        report.max_value = np.max(cast(np.ndarray, non_null_numeric_values))
        if isinstance(report.max_value, np.bool_):
            report.max_value = np.int8(report.max_value)
        report.values_domain = f"[{report.min_value}, {report.max_value}]"
    else:
        values = [v for v in report.unique_values if v.strip() != ""]
        report.values_domain = ", ".join(sorted(values))

    report.rank = report.count_unique_values

    if measure_type in [MeasureType.ordinal, MeasureType.continuous]:
        assert len(measure_values) == len(numeric_values)
        return numeric_values, report

    return measure_values, report
