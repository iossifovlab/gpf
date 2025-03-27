import enum
import itertools
from collections.abc import Sequence
from typing import Any, cast

import numpy as np
from pydantic import BaseModel

from dae.genomic_resources.histogram import (
    CategoricalHistogram,
    Histogram,
    NullHistogram,
    NumberHistogram,
)
from dae.pheno.common import InferenceConfig
from dae.pheno.utils.commons import remove_annoying_characters


def is_nan(val: Any) -> bool:
    """Check if the passed value is a NaN."""
    if val is None:
        return True
    if isinstance(val, str) and val.strip() == "":
        return True

    return bool(type(val) in {float, np.float64, np.float32} and np.isnan(val))


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


def convert_to_numeric(val: Any) -> float | np.float64:
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


class InferenceReport(BaseModel):
    """Inference results report."""
    value_type: type
    histogram_type: type[Histogram]
    min_individuals: int
    count_total: int
    count_with_values: int
    count_without_values: int
    count_unique_values: int
    min_value: float | int | None
    max_value: float | int | None
    values_domain: str


def convert_to_float(value: int | float | str | None) -> float | None:
    try:
        if value is not None:
            return float(value)
    except ValueError:
        return None
    return value


def convert_to_int(value: int | float | str | None) -> int | None:
    try:
        if value is not None:
            return int(value)
    except ValueError:
        return None
    return value


def determine_histogram_type(
    report: InferenceReport, config: InferenceConfig,
) -> type[Histogram]:
    """Given an inference report and a configuration, return histogram type."""
    if config.histogram_type is not None:
        if config.histogram_type == "number":
            return NumberHistogram
        if config.histogram_type == "categorical":
            return CategoricalHistogram
        return NullHistogram

    if (
        config.min_individuals is not None and
        report.count_with_values < config.min_individuals
    ):
        return NullHistogram

    is_numeric = report.value_type is not str

    if is_numeric:
        if (
            config.continuous.min_rank is not None and
            report.count_unique_values >= config.continuous.min_rank
        ):
            return NumberHistogram
        if (
            config.ordinal.min_rank is not None and
            report.count_unique_values >= config.ordinal.min_rank
        ):
            return CategoricalHistogram
    elif (
        report.count_unique_values is not None
        and config.categorical.min_rank is not None
        and config.categorical.max_rank is not None
        and report.count_unique_values >= config.categorical.min_rank
        and report.count_unique_values <= config.categorical.max_rank
    ):
        return CategoricalHistogram

    return NullHistogram


TransformedValuesType = \
    list[float | None] | list[int | None] | list[str | None]


def inference_reference_impl(
    values: list[str | None], config: InferenceConfig,
) -> tuple[
    TransformedValuesType,
    InferenceReport,
]:
    """Infer value and histogram type for a list of values."""
    if config.value_type is not None:
        return force_type_inference(values, config)
    current_value_type: type[int] | type[float] = int
    unique_values: set[str] = set()
    numeric_values: list[int | float | None] = []
    unique_numeric_values = set()
    min_value: int | float | None = None
    max_value: int | float | None = None
    count_total = len(values)
    numeric_count = 0
    none_count = 0

    for val in values:
        num_value: int | float | None = None
        if val is None:
            none_count += 1
            numeric_values.append(None)
            continue
        unique_values.add(val)
        try:
            num_value = current_value_type(val)
            numeric_values.append(num_value)
            numeric_count += 1
            unique_numeric_values.add(num_value)
            if min_value is None or min_value > num_value:
                min_value = num_value
            if max_value is None or max_value < num_value:
                max_value = num_value
        except ValueError:
            if current_value_type is int:
                to_float = convert_to_float(val)
                if to_float is not None:
                    current_value_type = float
                    numeric_values = list(
                        map(convert_to_float, numeric_values),
                    )
                    numeric_values.append(to_float)
                    numeric_count += 1
                    unique_numeric_values.add(to_float)
                    if min_value is None or min_value > to_float:
                        min_value = to_float
                    if max_value is None or max_value < to_float:
                        max_value = to_float
                    continue
                numeric_values.append(None)
            else:
                numeric_values.append(None)

    value_type: type[int] | type[float] | type[str] = current_value_type
    total_with_values = count_total - none_count
    non_numeric_count = total_with_values - numeric_count

    if total_with_values == 0:
        non_numeric = 0.0
    else:
        non_numeric = (
            1.0 * non_numeric_count / total_with_values
        )

    transformed_values: (
        Sequence[float | None] | Sequence[int | None] | Sequence[str | None]
    )

    if non_numeric > config.non_numeric_cutoff:
        value_type = str
        min_value = None
        max_value = None
        domain_values = list(itertools.islice(
            [v for v in sorted(unique_values) if v.strip() != ""],
            0,
            20,
        ))
        values_domain = ", ".join(sorted(domain_values))
        count_unique_values = len(unique_values)
        transformed_values = values
    else:
        none_count = non_numeric_count
        values_domain = f"[{min_value}, {max_value}]"
        count_unique_values = len(unique_numeric_values)
        transformed_values = numeric_values

    report = InferenceReport.model_validate({
        "value_type": value_type,
        "histogram_type": NullHistogram,
        "min_individuals": config.min_individuals,
        "count_total": count_total,
        "count_with_values": total_with_values,
        "count_without_values": none_count,
        "count_unique_values": count_unique_values,
        "min_value": min_value,
        "max_value": max_value,
        "values_domain": values_domain,
    })

    return transformed_values, report


def force_type_inference(
    values: list[str | None], config: InferenceConfig,
) -> tuple[TransformedValuesType, InferenceReport]:
    """Perform type inference when a type is forced."""
    count_total = len(values)
    transformed_values: TransformedValuesType = values
    if config.value_type == "str":
        value_type = str
    elif config.value_type == "int":
        value_type = int
        transformed_values = list(map(convert_to_int, values))
    elif config.value_type == "float":
        value_type = float
        transformed_values = list(map(convert_to_float, values))
    else:
        raise ValueError("Invalid value type")

    unique_values = set(transformed_values)

    if value_type is str:
        domain_values = list(itertools.islice(
            [
                v for v in cast(set[str | None], unique_values)
                if v is not None and v.strip() != ""
            ],
            0,
            20,
        ))
        min_value = None
        max_value = None
        values_domain = ", ".join(sorted(domain_values))
    else:
        non_null_values = cast(list[float | int], list(
            filter(lambda x: x is not None, unique_values),
        ))
        min_value = min(non_null_values)
        max_value = max(non_null_values)
        values_domain = f"[{min_value}, {max_value}]"

    count_without_values = len(list(
        filter(lambda v: v is None, transformed_values),
    ))
    count_with_values = count_total - count_without_values
    count_unique_values = len(set(values))
    inference_report = InferenceReport.model_validate({
        "value_type": value_type,
        "histogram_type": NullHistogram,
        "min_individuals": config.min_individuals,
        "count_total": count_total,
        "count_with_values": count_with_values,
        "count_without_values": count_without_values,
        "count_unique_values": count_unique_values,
        "min_value": min_value,
        "max_value": max_value,
        "values_domain": values_domain,
    })
    return transformed_values, inference_report
