"""Handling of genomic scores statistics.

Currently we support only genomic scores histograms.
"""
from __future__ import annotations

import copy
import logging
from typing import cast, Optional, Any, BinaryIO, Union
from dataclasses import dataclass

import yaml
import numpy as np

from dae.genomic_resources.statistics.base_statistic import Statistic
from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.statistics.min_max import MinMaxValue

logger = logging.getLogger(__name__)


class HistogramError(BaseException):
    """
    Class used for histogram specific errors.

    Histograms should be annulled when a HistogramError occurs.
    """

    # pylint: disable=unnecessary-pass
    pass


@dataclass
class NumberHistogramConfig:
    """Configuration class for number histograms."""

    view_range: tuple[Optional[float], Optional[float]]
    number_of_bins: int = 30
    x_log_scale: bool = False
    y_log_scale: bool = False
    x_min_log: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "number",
            "view_range": {
                "min": self.view_range[0],
                "max": self.view_range[1]
            },
            "number_of_bins": self.number_of_bins,
            "x_log_scale": self.x_log_scale,
            "y_log_scale": self.y_log_scale,
            "x_min_log": self.x_min_log
        }

    @staticmethod
    def convert_legacy_config(config: dict[str, Any]) -> NumberHistogramConfig:
        logger.warning("Converting legacy config")
        limits = np.iinfo(np.int64)
        return NumberHistogramConfig(
            view_range=(
                config.get("min", limits.min), config.get("max", limits.max)
            ),
            number_of_bins=config.get("bins", 30),
            x_log_scale=config.get("x_scale", "linear") == "log",
            y_log_scale=config.get("y_scale", "linear") == "log",
            x_min_log=config.get("x_min_log")
        )

    @staticmethod
    def from_dict(parsed: dict[str, Any]) -> NumberHistogramConfig:
        """Build a number histogram config from a parsed yaml file."""
        hist_type = parsed.get("type")
        if hist_type != "number":
            logger.error(
                "Invalid configuration type (%s)"
                " for number histogram!\n%s",
                hist_type, parsed
            )
            raise TypeError(
                "Invalid configuration for number histogram!\n"
                f"{parsed}"
            )
        yaml_range = parsed.get("view_range", {})
        x_min = yaml_range.get("min", None)
        x_max = yaml_range.get("max", None)
        view_range = (x_min, x_max)
        number_of_bins = parsed.get("number_of_bins", 100)
        x_log_scale = parsed.get("x_log_scale", False)
        y_log_scale = parsed.get("y_log_scale", False)
        x_min_log = parsed.get("x_min_log", None)
        return NumberHistogramConfig(
            view_range, number_of_bins,
            x_log_scale, y_log_scale,
            x_min_log
        )

    @staticmethod
    def default_config(min_max: MinMaxValue) -> NumberHistogramConfig:
        """Build a number histogram config from a parsed yaml file."""
        if min_max.min == min_max.max:
            view_range = (min_max.min, min_max.min + 1.0)
        else:
            view_range = (min_max.min, min_max.max)
        number_of_bins = 100
        x_log_scale = False
        y_log_scale = False
        return NumberHistogramConfig(
            view_range, number_of_bins, x_log_scale, y_log_scale)


@dataclass
class CategoricalHistogramConfig:
    """Configuration class for categorical histograms."""

    value_order: list[str]
    y_log_scale: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "categorical",
            "value_order": self.value_order,
            "y_log_scale": self.y_log_scale,
        }

    @staticmethod
    def default_config() -> CategoricalHistogramConfig:
        return CategoricalHistogramConfig([])

    @staticmethod
    def from_dict(parsed: dict[str, Any]) -> CategoricalHistogramConfig:
        """Create categorical histogram config from configuratin dict."""
        hist_type = parsed.get("type")
        if hist_type != "categorical":
            raise TypeError(
                "Invalid configuration type for categorical histogram!\n"
                f"{parsed}"
            )
        value_order = parsed.get("value_order", [])
        y_log_scale = parsed.get("y_log_scale", False)

        return CategoricalHistogramConfig(
            value_order=value_order,
            y_log_scale=y_log_scale,
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
                f"{parsed}"
            )
        reason = parsed.get("reason", "Unspecified reason")

        return NullHistogramConfig(
            reason=reason,
        )


class NumberHistogram(Statistic):
    """Class to represent a histogram."""

    # pylint: disable=too-many-instance-attributes
    # FIXME:
    def __init__(
            self, config: NumberHistogramConfig,
            bins: Optional[np.ndarray] = None,
            bars: Optional[np.ndarray] = None):
        super().__init__("histogram", "Collects values for histogram.")
        assert isinstance(config, NumberHistogramConfig)
        self.config = config
        self.out_of_range_values: list[float] = []
        self.out_of_range_bins: list[int] = [0, 0]

        self.min_value: float = np.nan
        self.max_value: float = np.nan

        if self.config.x_log_scale and self.config.x_min_log is None:
            raise ValueError(
                "Invalid histogram configuration, missing x_min_log"
            )
        if self.config.view_range[0] is None or \
                self.config.view_range[1] is None:
            logger.error(
                "unexpected min/max value: [%s, %s]",
                self.config.view_range[0], self.config.view_range[1])
            raise ValueError(
                "unexpected min/max value:"
                f"[{self.config.view_range[0]}, "
                f"{self.config.view_range[1]}]")

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
                        self.config.number_of_bins
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
        elif self.bins is None or self.bars is None:
            raise ValueError(
                "Cannot instantiate histogram with only bins or only bars!"
            )

    def view_min(self) -> float:
        if self.config.view_range[0] is None:
            raise ValueError("view range min value not set")
        return self.config.view_range[0]

    def view_max(self) -> float:
        if self.config.view_range[1] is None:
            raise ValueError("view range max value not set")
        return self.config.view_range[1]

    def merge(self, other: NumberHistogram) -> None:
        """Merge two histograms."""
        assert self.config == other.config
        assert self.bins is not None and self.bars is not None
        assert other.bins is not None and other.bars is not None

        assert all(self.bins == other.bins)

        self.bars += other.bars
        self.out_of_range_bins[0] += other.out_of_range_bins[0]
        self.out_of_range_bins[1] += other.out_of_range_bins[1]
        self.min_value = min(self.min_value, other.min_value)
        self.max_value = max(self.max_value, other.max_value)

    @property
    def view_range(self) -> tuple[Optional[float], Optional[float]]:
        return self.config.view_range

    def add_value(self, value: float) -> bool:
        """Add value to the histogram."""
        if value is None or np.isnan(value):
            return False

        if not isinstance(value, (int, float, np.integer)):
            raise TypeError(
                "Cannot add non numerical value "
                f"{value} ({type(value)}) to number histogram"
            )

        self.min_value = min(value, self.min_value)
        self.max_value = max(value, self.max_value)

        if self.config.x_log_scale:
            index = self.choose_bin_log(value)
        else:
            index = self.choose_bin_lin(value)
        if index < 0:
            logger.warning(
                "out of range %s value %s", self.view_range, value)
            tindex = index + 2
            self.out_of_range_bins[tindex] += 1
            return False

        self.bars[index] += 1
        return True

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
            "min_value": self.min_value,
            "max_value": self.max_value
        }

    def serialize(self) -> str:
        return cast(str, yaml.dump(self.to_dict()))

    def plot(self, outfile: BinaryIO, score_id: str) -> None:
        """Plot histogram and save it into outfile."""
        # pylint: disable=import-outside-toplevel
        import matplotlib.pyplot as plt
        width = self.bins[1:] - self.bins[:-1]
        plt.bar(
            x=self.bins[:-1], height=self.bars,
            log=self.config.y_log_scale,
            width=width,
            align="edge")

        if self.config.x_log_scale:
            plt.xscale("log")

        plt.xlabel(score_id)
        plt.ylabel("count")

        plt.grid(axis="y")
        plt.grid(axis="x")

        plt.savefig(outfile)
        plt.clf()

    @staticmethod
    def deserialize(data: str) -> NumberHistogram:
        res = yaml.load(data, yaml.Loader)
        config = NumberHistogramConfig.from_dict(res.get("config"))

        hist = NumberHistogram(
            config,
            bins=np.array(res.get("bins")),
            bars=np.array(res.get("bars"))
        )
        hist.min_value = res.get("min_value", np.nan)
        hist.max_value = res.get("max_value", np.nan)
        hist.out_of_range_bins = res.get("out_of_range_bins", [0, 0])

        return hist


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

    def __init__(self, config: Optional[NullHistogramConfig]) -> None:
        super().__init__(
            "null_histogram", "Used for invalid/annulled histograms"
        )
        if config is None:
            config = NullHistogramConfig.default_config()
        self.reason = config.reason

    def add_value(self, value: Any) -> bool:
        return False

    def merge(self, other: Any) -> None:
        return

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "null",
            "reason": self.reason
        }

    # pylint: disable=unused-argument
    def plot(self, outfile: BinaryIO, score_id: str) -> None:
        return

    def serialize(self) -> str:
        return cast(str, yaml.dump(
            self.to_dict()
        ))

    @staticmethod
    def deserialize(data: str) -> NullHistogram:
        res = yaml.load(data, yaml.Loader)
        hist_type = res.get("type")
        if hist_type != "null":
            raise TypeError(
                f"Invalid configuration type for null histogram!\n{data}"
            )

        reason = res.get("reason", "")

        return NullHistogram(NullHistogramConfig(reason=reason))


class CategoricalHistogram(Statistic):
    """Class for categorical data histograms."""

    VALUES_LIMIT = 100

    # pylint: disable=too-few-public-methods
    def __init__(
        self,
        config: CategoricalHistogramConfig,
        values: Optional[dict[str, int]] = None
    ):
        super().__init__(
            "categorical_histogram",
            "Collects values for categorical histogram."
        )
        self.config = config
        self.values = {}
        if values is not None:
            self.values = values
        for value in config.value_order:
            if value not in self.values:
                self.values[value] = 0
        self.y_log_scale = config.y_log_scale

    def add_value(self, value: Optional[str]) -> bool:
        """Add a value to the categorical histogram.

        Returns true if successfully added and false if failed.
        Will fail if too many values are accumulated.
        """
        if value is None:
            return False
        if not isinstance(value, str):
            raise TypeError(
                "Cannot add non string value "
                f"{value} to categorical histogram"
            )
        if value not in self.values:
            if len(self.values) + 1 > CategoricalHistogram.VALUES_LIMIT:
                raise HistogramError(
                    f"Too many values already present to add {value}"
                    " to categorical histogram."
                )
            self.values[value] = 1
        else:
            self.values[value] += 1

        return True

    def merge(self, other: CategoricalHistogram) -> None:
        """Merge with other histogram."""
        assert self.config == other.config

        for value, count in other.values.items():
            if value not in self.values:
                if len(self.values) + 1 > CategoricalHistogram.VALUES_LIMIT:
                    raise HistogramError(
                        f"Too many values already present to merge {value}"
                        " to categorical histogram."
                    )
                self.values[value] = count
            else:
                self.values[value] += count

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "values": self.values
        }

    def serialize(self) -> str:
        return cast(str, yaml.dump(self.to_dict()))

    @staticmethod
    def deserialize(data: str) -> CategoricalHistogram:
        res = yaml.load(data, yaml.Loader)
        config = CategoricalHistogramConfig.from_dict(res.get("config"))
        return CategoricalHistogram(config, res.get("values"))

    def plot(self, outfile: BinaryIO, score_id: str) -> None:
        """Plot histogram and save it into outfile."""
        # pylint: disable=import-outside-toplevel
        import matplotlib.pyplot as plt
        values = self.values.keys()
        counts = self.values.values()
        plt.figure(figsize=(15, 10), tight_layout=True)
        plt.bar(values, counts)

        plt.xlabel(score_id)
        plt.ylabel("count")

        plt.tick_params(axis="x", labelrotation=90)

        plt.savefig(outfile)
        plt.clf()


# def annul_histogram(
#     histogram: Union[NumberHistogram, CategoricalHistogram]
# ) -> NullHistogram:
#     return NullHistogram(NullHistogramConfig.default_config())


def build_histogram_config(
    config: Optional[dict[str, Any]]) -> Union[
    NumberHistogramConfig, CategoricalHistogramConfig,
    NullHistogramConfig, None
]:
    """Create histogram config form configuration dict."""
    if config is None:
        return None
    if "histogram" in config:
        hist_config = config["histogram"]
        hist_type = hist_config["type"]
    elif "number_hist" in config:
        hist_type = "number"
        hist_config = copy.copy(config["number_hist"])
        hist_config["type"] = hist_type
    elif "categorical_hist" in config:
        hist_type = "categorical"
        hist_config = copy.copy(config["categorical_hist"])
        hist_config["type"] = hist_type
    elif "null_hist" in config:
        hist_type = "null"
        hist_config = copy.copy(config["null_hist"])
        hist_config["type"] = hist_type
    else:
        return None

    if hist_type == "number":
        return NumberHistogramConfig.from_dict(hist_config)
    if hist_type == "categorical":
        return CategoricalHistogramConfig.from_dict(hist_config)
    if hist_type == "null":
        return NullHistogramConfig.from_dict(hist_config)

    return NullHistogramConfig(f"Invalid histogram configuration {config}")


def build_empty_histogram(
    config: Union[
        NumberHistogramConfig, CategoricalHistogramConfig,
        NullHistogramConfig, None
    ], **kwargs: Any
) -> Union[NumberHistogram, CategoricalHistogram, NullHistogram]:
    """Create an empty histogram from a deserialize histogram dictionary."""
    # pylint: disable=too-many-return-statements
    if config is None:
        # create default histogram config
        value_type = kwargs.get("value_type")
        if value_type in ["int", "float"]:
            min_max = kwargs.get("min_max")
            if min_max is not None and min_max.min is not None and \
                    min_max.max is not None:
                return NumberHistogram(
                    NumberHistogramConfig.default_config(min_max)
                )
        if value_type == "str":
            return CategoricalHistogram(
                CategoricalHistogramConfig.default_config()
            )
        return NullHistogram(NullHistogramConfig(
            "No histogram configured and no default config available for type"
            f"{value_type}"
        ))

    try:
        if isinstance(config, NumberHistogramConfig):
            return NumberHistogram(config)
        if isinstance(config, CategoricalHistogramConfig):
            return CategoricalHistogram(config)
        if isinstance(config, NullHistogramConfig):
            return NullHistogram(config)
        return NullHistogram(NullHistogramConfig(
            "Could not match histogram config type"
        ))
    except BaseException:  # pylint: disable=broad-except
        logger.warning("Failed to create empty histogram from config")
        return NullHistogram(NullHistogramConfig(
            "Failed to create empty histogram from config."))


def load_histogram(  # pylint: disable=too-many-return-statements
    config: Union[
        NumberHistogramConfig, CategoricalHistogramConfig,
        NullHistogramConfig, None
    ],
    resource: GenomicResource, filename: str
) -> Union[NumberHistogram, CategoricalHistogram, NullHistogram]:
    """
    Try and load and return a histogram in a resource.

    On an error or missing histogram, an appropriate NullHistogram is returned.
    """
    # if config is None:
    #     return NullHistogram(NullHistogramConfig("No histogram configured"))

    try:
        with resource.open_raw_file(filename) as infile:
            content = infile.read()
    except FileNotFoundError:
        logger.warning(
            "unable to load histogram file: %s",
            filename)
        return NullHistogram(NullHistogramConfig(
            f"Could not load file {filename}"
        ))

    try:
        if isinstance(config, NumberHistogramConfig):
            return NumberHistogram.deserialize(content)
        if isinstance(config, CategoricalHistogramConfig):
            return CategoricalHistogram.deserialize(content)
        if isinstance(config, NullHistogramConfig):
            return NullHistogram.deserialize(content)

        return NullHistogram(NullHistogramConfig("Invalid histogram type"))
    except BaseException:  # pylint: disable=broad-except
        logger.exception(
            "Failed to deserialize histogram from %s",
            filename
        )
        return NullHistogram(NullHistogramConfig(
            "Failed to deserialize histogram."
        ))
