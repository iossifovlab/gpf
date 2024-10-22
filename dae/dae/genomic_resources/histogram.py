"""Handling of genomic scores statistics.

Currently we support only genomic scores histograms.
"""
from __future__ import annotations

import importlib
import logging
import pathlib
import sys
from collections import Counter
from dataclasses import dataclass
from typing import IO, Any

import numpy as np
import yaml

from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.statistics.base_statistic import Statistic
from dae.genomic_resources.statistics.min_max import MinMaxValue

logger = logging.getLogger(__name__)


class HistogramError(BaseException):
    """
    Class used for histogram specific errors.

    Histograms should be nullified when a HistogramError occurs.
    """


@dataclass
class NumberHistogramConfig:
    """Configuration class for number histograms."""

    view_range: tuple[float | None, float | None]
    number_of_bins: int = 100
    x_log_scale: bool = False
    y_log_scale: bool = False
    x_min_log: float | None = None
    plot_function: str | None = None

    def has_view_range(self) -> bool:
        return self.view_range[0] is not None and \
            self.view_range[1] is not None

    def to_dict(self) -> dict[str, Any]:
        """Transform number histogram config to dict."""
        result = {
            "type": "number",
            "view_range": {
                "min": self.view_range[0],
                "max": self.view_range[1],
            },
            "number_of_bins": self.number_of_bins,
            "x_log_scale": self.x_log_scale,
            "y_log_scale": self.y_log_scale,
            "x_min_log": self.x_min_log,
        }
        if self.plot_function is not None:
            result["plot_function"] = self.plot_function

        return result

    @staticmethod
    def from_dict(parsed: dict[str, Any]) -> NumberHistogramConfig:
        """Build a number histogram config from a parsed yaml file."""
        hist_type = parsed.get("type")
        if hist_type != "number":
            logger.error(
                "Invalid configuration type (%s)"
                " for number histogram!\n%s",
                hist_type, parsed,
            )
            raise TypeError(
                "Invalid configuration for number histogram!\n"
                f"{parsed}",
            )
        yaml_range = parsed.get("view_range", {})
        x_min = yaml_range.get("min", None)
        x_max = yaml_range.get("max", None)
        view_range = (x_min, x_max)
        number_of_bins = parsed.get("number_of_bins", 100)
        x_log_scale = parsed.get("x_log_scale", False)
        y_log_scale = parsed.get("y_log_scale", False)
        x_min_log = parsed.get("x_min_log")
        plot_function = parsed.get("plot_function")

        return NumberHistogramConfig(
            view_range, number_of_bins,
            x_log_scale, y_log_scale,
            x_min_log,
            plot_function=plot_function,
        )

    @staticmethod
    def default_config(
        min_max: MinMaxValue | None,
    ) -> NumberHistogramConfig:
        """Build a number histogram config from a parsed yaml file."""
        if min_max is None:
            view_range: tuple[float | None, float | None] = (None, None)
        elif min_max.min == min_max.max:
            view_range = (min_max.min, min_max.min + 1.0)
        else:
            view_range = (min_max.min, min_max.max)
        number_of_bins = 100
        x_log_scale = False
        y_log_scale = False
        return NumberHistogramConfig(
            view_range, number_of_bins, x_log_scale, y_log_scale)


DEFAULT_DISPLAYED_VALUES_COUNT = 20


@dataclass
class CategoricalHistogramConfig:
    """Configuration class for categorical histograms."""
    displayed_values_count: int | None = 20
    displayed_values_percent: float | None = None
    value_order: list[str | int] | None = None
    y_log_scale: bool = False
    plot_function: str | None = None
    enforce_type: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Transform categorical histogram config to dict."""
        result: dict[str, Any] = {
            "type": "categorical",
            "value_order": self.value_order,
            "y_log_scale": self.y_log_scale,
        }
        if self.displayed_values_count != DEFAULT_DISPLAYED_VALUES_COUNT:
            result["displayed_values_count"] = self.displayed_values_count
        if self.displayed_values_percent is not None:
            result["displayed_values_percent"] = \
                self.displayed_values_percent
        if self.plot_function is not None:
            result["plot_function"] = self.plot_function
        return result

    @staticmethod
    def default_config() -> CategoricalHistogramConfig:
        return CategoricalHistogramConfig(enforce_type=False)

    @staticmethod
    def from_dict(parsed: dict[str, Any]) -> CategoricalHistogramConfig:
        """Create categorical histogram config from configuratin dict."""
        hist_type = parsed.get("type")
        if hist_type != "categorical":
            raise TypeError(
                "Invalid configuration type for categorical histogram!\n"
                f"{parsed}",
            )
        displayed_values_count = parsed.get(
            "displayed_values_count")
        displayed_values_percent = parsed.get(
            "displayed_values_percent")
        if displayed_values_count is not None \
                and displayed_values_percent is not None:
            raise ValueError(
                "Invalid configuration for categorical histogram: "
                "displayed_values_count and displayed_values_percent "
                "cannot be both set\n"
                f"{parsed}",
            )

        if displayed_values_percent is None and displayed_values_count is None:
            displayed_values_count = DEFAULT_DISPLAYED_VALUES_COUNT

        value_order = parsed.get("value_order", [])
        y_log_scale = parsed.get("y_log_scale", False)
        plot_function = parsed.get("plot_function")

        return CategoricalHistogramConfig(
            displayed_values_count=displayed_values_count,
            displayed_values_percent=displayed_values_percent,
            value_order=value_order,
            y_log_scale=y_log_scale,
            plot_function=plot_function,
            enforce_type=True,
        )


@dataclass
class NullHistogramConfig:
    """Configuration class for null histograms."""

    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "null",
            "reason": self.reason,
        }

    @staticmethod
    def default_config() -> NullHistogramConfig:
        return NullHistogramConfig("Unspecified reason")

    @staticmethod
    def from_dict(parsed: dict[str, Any]) -> NullHistogramConfig:
        """Create Null histogram from configuration dict."""
        hist_type = parsed.get("type")
        if hist_type != "null":
            raise TypeError(
                "Invalid configuration type for null histogram!\n"
                f"{parsed}",
            )
        reason = parsed.get("reason", "Unspecified reason")

        return NullHistogramConfig(
            reason=reason,
        )


class NumberHistogram(Statistic):
    """Class to represent a histogram."""

    type = "number_histogram"

    def __init__(
            self, config: NumberHistogramConfig,
            bins: np.ndarray | None = None,
            bars: np.ndarray | None = None):
        super().__init__("histogram", "Collects values for histogram.")
        logger.debug("number histogram config: %s", config)

        assert isinstance(config, NumberHistogramConfig)
        self.config = config
        self.out_of_range_values: list[float] = []
        self.out_of_range_bins: list[int] = [0, 0]

        self.min_value: float = np.nan
        self.max_value: float = np.nan
        self.choose_bin_index = self.choose_bin_lin
        if self.config.x_log_scale:
            self.choose_bin_index = self.choose_bin_log

        if self.config.x_log_scale and self.config.x_min_log is None:
            raise ValueError(
                "Invalid histogram configuration, missing x_min_log",
            )
        if self.config.view_range[0] is None or \
                self.config.view_range[1] is None or \
                np.isnan(self.config.view_range[0]) or \
                np.isnan(self.config.view_range[1]):
            logger.error(
                "unexpected min/max value: [%s, %s]",
                self.config.view_range[0], self.config.view_range[1])
            raise ValueError(
                "unexpected min/max value:"
                f"[{self.config.view_range[0]}, "
                f"{self.config.view_range[1]}]")

        self.view_range: tuple[float, float] = (
            self.config.view_range[0], self.config.view_range[1])

        if bins is not None and bars is not None:
            self.bins = bins
            self.bars = bars
        elif bins is None and bars is None:
            if self.config.x_log_scale:
                assert self.config.x_min_log is not None
                self.bins = np.array([
                    self.config.view_range[0],
                    * np.logspace(
                        np.log10(self.config.x_min_log),
                        np.log10(self.config.view_range[1]),
                        self.config.number_of_bins,
                    )])
                self._rstep = (self.config.number_of_bins - 1) / \
                    (np.log10(self.view_max())
                     - np.log10(self.config.x_min_log))
            else:
                self.bins = np.linspace(
                    self.config.view_range[0],
                    self.config.view_range[1],
                    self.config.number_of_bins + 1,
                )
                self._rstep = self.config.number_of_bins / \
                    (self.view_max() - self.view_min())
            self.bars = np.zeros(self.config.number_of_bins, dtype=np.int64)
            assert not np.any(np.isnan(self.bins)), ("nan bins", self.config)
        elif self.bins is None or self.bars is None:
            raise ValueError(
                "Cannot instantiate histogram with only bins or only bars!",
            )

    def view_min(self) -> float:
        return self.view_range[0]

    def view_max(self) -> float:
        return self.view_range[1]

    def merge(self, other: Statistic) -> None:
        """Merge two histograms."""
        assert isinstance(other, NumberHistogram)
        assert self.bins is not None
        assert self.bars is not None
        assert other.bins is not None
        assert other.bars is not None

        assert np.allclose(self.bins, other.bins, rtol=1e-5), \
            (self.bins, other.bins)

        self.bars += other.bars
        self.out_of_range_bins[0] += other.out_of_range_bins[0]
        self.out_of_range_bins[1] += other.out_of_range_bins[1]
        if np.isnan(self.min_value):
            self.min_value = min(other.min_value, self.min_value)
        else:
            self.min_value = min(self.min_value, other.min_value)
        if np.isnan(self.max_value):
            self.max_value = max(other.max_value, self.max_value)
        else:
            self.max_value = max(self.max_value, other.max_value)

    def values_domain(self) -> str:
        return f"[{self.min_value:0.3f}, {self.max_value:0.3f}]"

    def add_value(self, value: float | None) -> None:
        """Add value to the histogram."""
        if value is None or np.isnan(value):
            return

        if not isinstance(value, (int, float, np.integer)):
            raise TypeError(
                "Cannot add non numerical value "
                f"{value} ({type(value)}) to number histogram",
            )

        self.min_value = min(value, self.min_value)
        self.max_value = max(value, self.max_value)

        index = self.choose_bin_index(value)
        if index < 0:
            logger.warning(
                "out of range %s value %s", self.view_range, value)
            tindex = index + 2
            self.out_of_range_bins[tindex] += 1
            return

        self.bars[index] += 1

    def choose_bin_lin(self, value: float) -> int:
        """Compute bin index for a passed value for linear x-scale."""
        if value < self.view_min():
            return -2
        if value > self.view_max():
            return -1
        index = int((value - self.view_min()) * self._rstep)
        return min(index, self.config.number_of_bins - 1)

    def choose_bin_log(self, value: float) -> int:
        """Compute bin index for a passed value for log x-scale."""
        assert self.config.x_log_scale
        assert self.config.x_min_log is not None

        if value < self.view_min():
            return -2
        if value > self.view_max():
            return -1

        if value < self.config.x_min_log:
            return 0

        index = int(
            (np.log10(value) - np.log10(self.config.x_min_log))
            * self._rstep) + 1
        return min(index, self.config.number_of_bins - 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "bins": self.bins.tolist(),
            "bars": self.bars.tolist(),
            "out_of_range_bins": self.out_of_range_bins,
            "min_value": float(self.min_value),
            "max_value": float(self.max_value),
        }

    def serialize(self) -> str:
        return yaml.dump(self.to_dict())

    def plot(
        self,
        outfile: IO,
        score_id: str,
        small_values_description: str | None = None,
        large_values_description: str | None = None,
    ) -> None:
        """Plot histogram and save it into outfile."""
        # pylint: disable=import-outside-toplevel
        import matplotlib
        matplotlib.use("agg")
        import matplotlib.pyplot as plt
        width = self.bins[1:] - self.bins[:-1]

        _, ax = plt.subplots()
        ax.bar(
            x=self.bins[:-1], height=self.bars,
            log=self.config.y_log_scale,
            width=width,
            align="edge")

        if self.config.x_log_scale:
            plt.xscale("log")

        if small_values_description is not None and \
            large_values_description is not None:

            sec = ax.secondary_xaxis(location=0)
            sec.set_ticks(
                [
                    self.bins[0],
                    self.bins[-1],
                ],
                labels=[
                    f"\n{small_values_description}",
                    f"\n{large_values_description}",
                ],
                wrap=True,
                color="gray",
                style="italic",
            )

        plt.xlabel(f"\n{score_id}")
        plt.ylabel("count")

        plt.grid(axis="y")
        plt.grid(axis="x")

        plt.tight_layout()

        plt.savefig(outfile)
        plt.clf()

    @staticmethod
    def from_dict(data: dict[str, Any]) -> NumberHistogram:
        """Build a number histogram from a dict."""
        config = NumberHistogramConfig.from_dict(data["config"])

        hist = NumberHistogram(
            config,
            bins=np.array(data.get("bins")),
            bars=np.array(data.get("bars")),
        )
        hist.min_value = data.get("min_value", np.nan)
        hist.max_value = data.get("max_value", np.nan)
        hist.out_of_range_bins = data.get("out_of_range_bins", [0, 0])

        return hist

    @staticmethod
    def deserialize(content: str) -> NumberHistogram:
        data = yaml.safe_load(content)
        return NumberHistogram.from_dict(data)


class HistogramStatisticMixin:
    """Mixin for creating statistics classes with histograms."""

    @staticmethod
    def get_histogram_file(score_id: str) -> str:
        return f"histogram_{score_id}.yaml"

    @staticmethod
    def get_histogram_image_file(score_id: str) -> str:
        return f"histogram_{score_id}.png"


class NullHistogram(Statistic):
    """Class for annulled histograms."""

    type = "null_histogram"

    def __init__(self, config: NullHistogramConfig | None) -> None:
        super().__init__(
            "null_histogram", "Used for invalid/annulled histograms",
        )
        if config is None:
            config = NullHistogramConfig.default_config()
        self.reason = config.reason

    def add_value(self, _value: Any) -> None:
        return

    def merge(self, _other: Any) -> None:
        return

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "type": "null",
                "reason": self.reason,
            },
        }

    def values_domain(self) -> str:
        return "NO DOMAIN"

    # pylint: disable=unused-argument
    def plot(self, _outfile: IO, _score_id: str) -> None:
        return

    def serialize(self) -> str:
        return yaml.dump(self.to_dict())

    @staticmethod
    def from_dict(data: dict[str, Any]) -> NullHistogram:
        """Build a null histogram from a dict."""
        config = data["config"]
        hist_type = config.get("type")
        if hist_type != "null":
            raise TypeError(
                f"Invalid configuration type for null histogram!\n{data}",
            )
        reason = config.get("reason", "")
        return NullHistogram(NullHistogramConfig(reason=reason))

    @staticmethod
    def deserialize(content: str) -> NullHistogram:
        data = yaml.safe_load(content)
        return NullHistogram.from_dict(data)


class CategoricalHistogram(Statistic):
    """Class for categorical data histograms."""

    type = "categorical_histogram"

    UNIQUE_VALUES_LIMIT = 100

    # pylint: disable=too-few-public-methods
    def __init__(
        self,
        config: CategoricalHistogramConfig,
        counter: dict[str | int, int] | None = None,
    ):
        super().__init__(
            "categorical_histogram",
            "Collects values for categorical histogram.",
        )
        self.config = config
        self.enforce_type = config.enforce_type

        if counter is not None:
            self._counter = Counter(counter)
        else:
            self._counter = Counter()

        self.y_log_scale = config.y_log_scale

    def add_value(self, value: str | int | None) -> None:
        """Add a value to the categorical histogram.

        Returns true if successfully added and false if failed.
        Will fail if too many values are accumulated.
        """
        if value is None:
            return
        if not isinstance(value, str | int):
            raise TypeError(
                "Only string or int values can be added categorical histogram; "
                f"bad <{value}>",
            )
        self._counter[value] += 1
        if not self.enforce_type and \
                len(self._counter) > CategoricalHistogram.UNIQUE_VALUES_LIMIT:
            raise HistogramError(
                f"Too many unique values {len(self._counter)} "
                f"for categorical histogram.",
            )

    def merge(self, other: Statistic) -> None:
        """Merge with other histogram."""
        assert isinstance(other, CategoricalHistogram)
        assert self.config == other.config
        # pylint: disable=protected-access
        self._counter += other._counter  # noqa: SLF001
        if not self.enforce_type and \
                len(self._counter) > CategoricalHistogram.UNIQUE_VALUES_LIMIT:
            raise HistogramError(
                f"Can not merge categorical histograms; "
                f"too many unique values {len(self._counter)}")

    @property
    def raw_values(self) -> dict[str | int, int]:
        return dict(self._counter)

    @property
    def display_values(self) -> dict[str | int, int]:
        """Return categorical histogram display values in order."""
        values = {}
        if self.config.value_order:
            for key in self.config.value_order:
                values[key] = self._counter[key]
            if len(values) < len(self._counter):
                raise ValueError(
                    "misconfigured categorical histogram value_order",
                    f"{self.config.value_order} < {self._counter.keys()}")
            return values

        if self.config.displayed_values_percent is not None:
            total = sum(self._counter.values())
            displayed = 0
            other = 0
            displayed_percent = self.config.displayed_values_percent
            for key, count in self._counter.most_common():
                if 100.0 * displayed / total < displayed_percent:
                    values[key] = count
                    displayed += count
                else:
                    other += count
            if other > 0:
                values["Other Values"] = other
            return values

        for key, count in self._counter.most_common(
                n=self.config.displayed_values_count):
            if key not in values:
                values[key] = count
        if self.config.displayed_values_count is not None and \
                len(self._counter) > self.config.displayed_values_count:
            other = 0
            for key, count in self._counter.items():
                if key not in values:
                    other += count
            if other > 0:
                values["Other Values"] = other
        return values

    def values_domain(self) -> str:
        return ", ".join(str(k) for k in self.display_values)

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "values": dict(self._counter),
        }

    def serialize(self) -> str:
        return yaml.dump(self.to_dict())

    @staticmethod
    def from_dict(data: dict[str, Any]) -> CategoricalHistogram:
        config = CategoricalHistogramConfig.from_dict(data["config"])
        return CategoricalHistogram(config, data.get("values"))

    @staticmethod
    def deserialize(content: str) -> CategoricalHistogram:
        data = yaml.safe_load(content)
        return CategoricalHistogram.from_dict(data)

    def plot(
        self,
        outfile: IO,
        score_id: str,
        small_values_description: str | None = None,
        large_values_description: str | None = None,
    ) -> None:
        """Plot histogram and save it into outfile."""
        # pylint: disable=import-outside-toplevel
        import matplotlib
        matplotlib.use("agg")
        import matplotlib.pyplot as plt
        display_values = self.display_values
        values = [str(k) for k in display_values]
        counts = list(display_values.values())

        plt.figure(figsize=(15, 10), tight_layout=True)

        _, ax = plt.subplots()
        ax.bar(
            x=values,
            height=counts,
            tick_label=[str(v) for v in values],
            log=self.config.y_log_scale,
            align="center",
        )

        if small_values_description is not None and \
            large_values_description is not None:

            sec = ax.secondary_xaxis(location=0)
            sec.set_ticks(
                [
                    0,
                    len(values) - 1,
                ],
                labels=[
                    f"\n{small_values_description}",
                    f"\n{large_values_description}",
                ],
                wrap=True,
                color="gray",
                style="italic",
            )

        plt.xlabel(f"\n{score_id}")
        plt.ylabel("count")

        plt.tick_params(axis="x", labelrotation=90)

        plt.tight_layout()

        plt.savefig(outfile)
        plt.clf()


def build_histogram_config(
        config: dict[str, Any] | None) -> HistogramConfig | None:
    """Create histogram config form configuration dict."""
    if config is None:
        return None
    if "histogram" in config:
        hist_config = config["histogram"]
        hist_type = hist_config["type"]
    else:
        return None

    if hist_type == "number":
        return NumberHistogramConfig.from_dict(hist_config)
    if hist_type == "categorical":
        return CategoricalHistogramConfig.from_dict(hist_config)
    if hist_type == "null":
        return NullHistogramConfig.from_dict(hist_config)

    return NullHistogramConfig(f"Invalid histogram configuration {config}")


def build_default_histogram_conf(
    value_type: str, **kwargs: Any,
) -> NumberHistogramConfig | CategoricalHistogramConfig | NullHistogramConfig:
    """Build default histogram config for given value type."""
    if value_type in ["int", "float"]:
        min_max = kwargs.get("min_max")
        return NumberHistogramConfig.default_config(min_max)

    if value_type == "str":
        return CategoricalHistogramConfig.default_config()

    return NullHistogramConfig(
        "No histogram configured and no default config available for type"
        f"{value_type}",
    )


def build_empty_histogram(
    config: HistogramConfig,
) -> NumberHistogram | CategoricalHistogram | NullHistogram:
    """Create an empty histogram from a deserialize histogram dictionary."""
    # pylint: disable=broad-except
    try:
        if isinstance(config, NumberHistogramConfig):
            return NumberHistogram(config)
        if isinstance(config, CategoricalHistogramConfig):
            return CategoricalHistogram(config)
        if isinstance(config, NullHistogramConfig):
            return NullHistogram(config)
        return NullHistogram(NullHistogramConfig(
            "Could not match histogram config type",
        ))
    except BaseException as err:  # noqa: BLE001
        logger.warning(
            "Failed to create empty histogram from config", exc_info=True)
        return NullHistogram(NullHistogramConfig(
            f"Failed to create empty histogram from config: {err}"))


def load_histogram(
    resource: GenomicResource, filename: str,
) -> Histogram:
    """Load and return a histogram in a resource.

    On an error or missing histogram, an appropriate NullHistogram is returned.
    """
    try:
        with resource.open_raw_file(filename) as infile:
            content = infile.read()
    except FileNotFoundError:
        logger.exception(
            "unable to load histogram file: %s; file not found", filename)
        return NullHistogram(NullHistogramConfig(
            "Histogram file not found.",
        ))

    hist_data = yaml.safe_load(content)
    config = hist_data["config"]
    hist_type = config["type"]
    try:
        if hist_type == "number":
            return NumberHistogram.deserialize(content)
        if hist_type == "categorical":
            return CategoricalHistogram.deserialize(content)
        if hist_type == "null":
            return NullHistogram.deserialize(content)

        return NullHistogram(NullHistogramConfig("Invalid histogram type"))
    except BaseException:  # pylint: disable=broad-except
        logger.exception(
            "Failed to deserialize histogram from %s",
            filename,
        )
        return NullHistogram(NullHistogramConfig(
            "Failed to deserialize histogram.",
        ))


HistogramConfig = \
    NullHistogramConfig | CategoricalHistogramConfig | NumberHistogramConfig
Histogram = NullHistogram | CategoricalHistogram | NumberHistogram


def _import_from_string(module_name: str, source_code: str) -> Any:
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    exec(source_code, module.__dict__)  # noqa: S102 pylint: disable=exec-used
    sys.modules[spec.name] = module
    return module


def plot_histogram(
    res: GenomicResource,
    image_filename: str,
    hist: Histogram,
    score_id: str,
    small_values_desc: str | None = None,
    large_values_desc: str | None = None,
) -> None:
    """Plot histogram and save it into the resource."""
    if isinstance(hist, NullHistogram):
        return

    if hist.config.plot_function is None:
        with res.open_raw_file(image_filename, mode="wb") as outfile:
            hist.plot(
                outfile,
                score_id,
                small_values_desc,
                large_values_desc,
            )
        return

    plot_file, plot_function_name = hist.config.plot_function.split(":")
    with res.open_raw_file(
        plot_file,
        mode="rt",
    ) as srcfile:
        source_code = srcfile.read()
        plot_module_name = str(
            pathlib.Path(res.resource_id) /
            pathlib.Path(plot_file).with_suffix("")).replace("/", ".")
        plot_module = _import_from_string(
            plot_module_name, source_code)
        func = getattr(plot_module, plot_function_name)

    with res.open_raw_file(
        image_filename,
        mode="wb",
    ) as outfile:
        func(
            outfile,
            hist,
            score_id,
            small_values_desc,
            large_values_desc,
        )

    return
