"""Handling of genomic scores statistics.

Currently we support only genomic scores histograms.
"""
from __future__ import annotations
from dataclasses import dataclass

import logging
from typing import cast, Optional, Any, BinaryIO, Union

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

    view_range: tuple[Optional[int], Optional[int]]
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
            #  raise TypeError(
            #      f"Invalid configuration type ({hist_type})"
            #      f" for number histogram!\n{parsed}"
            #  )
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
    def __init__(self, config: NumberHistogramConfig, bins=None, bars=None):
        super().__init__("histogram", "Collects values for histogram.")
        assert isinstance(config, NumberHistogramConfig)
        self.config = config
        self.bins = bins
        self.bars = bars
        self.out_of_range_values: list[float] = []

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

        if self.bins is None and self.bars is None:
            if self.config.x_log_scale:
                assert self.config.x_min_log is not None
                self.bins = np.array([
                    self.config.view_range[0],
                    * np.logspace(
                        np.log10(self.config.x_min_log),
                        np.log10(self.config.view_range[1]),
                        self.config.number_of_bins
                    )])
            else:
                self.bins = np.linspace(
                    self.config.view_range[0],
                    self.config.view_range[1],
                    self.config.number_of_bins + 1,
                )
            self.bars = np.zeros(self.config.number_of_bins, dtype=np.int64)
        elif self.bins is None or self.bars is None:
            raise ValueError(
                "Cannot instantiate histogram with only bins or only bars!"
            )

    def merge(self, other: NumberHistogram) -> None:
        """Merge two histograms."""
        assert self.config == other.config
        assert all(self.bins == other.bins)

        self.bars += other.bars
        self.out_of_range_values.extend(other.out_of_range_values)

    @property
    def view_range(self) -> tuple[Optional[int], Optional[int]]:
        return self.config.view_range

    def add_value(self, value: float) -> bool:
        """Add value to the histogram."""

        if value is None:
            return False

        if np.isnan(value):
            return False

        if not isinstance(value, (int, float, np.integer)):
            raise TypeError(
                "Cannot add non numerical value "
                f"{value} ({type(value)}) to number histogram"
            )

        if (
            self.config.view_range[0] is not None
            and value < self.config.view_range[0]
        ) or (
            self.config.view_range[1] is not None
            and value > self.config.view_range[1]
        ):
            logger.warning(
                "value %s out of range: [%s, %s];",
                value, self.config.view_range[0], self.config.view_range[1])
            self.out_of_range_values.append(value)
            return False

        index = self.bins.searchsorted(value, side="right")
        if index == 0:
            logger.warning(
                "(1) empty index %s for value %s",
                index, value)
            return False
        if value == self.bins[-1]:
            self.bars[-1] += 1
            return True

        self.bars[index - 1] += 1
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "bins": self.bins.tolist(),
            "bars": self.bars.tolist()
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
        # assert res["config"]["type"] == "number"

        config = NumberHistogramConfig.from_dict(res.get("config"))

        return NumberHistogram(
            config,
            bins=np.array(res.get("bins")),
            bars=np.array(res.get("bars"))
        )


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

    # pylint: disable=unused-argument,no-self-use
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

        return NullHistogram(reason=reason)


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
        """
        Add a value to the categorical histogram.

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
        plt.bar(values, counts)

        plt.xlabel(score_id)
        plt.ylabel("count")

        plt.savefig(outfile)
        plt.clf()


def annul_histogram(
    histogram: Union[NumberHistogram, CategoricalHistogram]
) -> NullHistogram:
    return NullHistogram(NullHistogramConfig.default_config())


def create_histogram_config_from_dict(
    config: Optional[dict[str, Any]]) -> Union[
    NumberHistogramConfig, CategoricalHistogramConfig,
    NullHistogramConfig, None
]:
    if config is None:
        return None
    hist_type = config.get("type")
    if hist_type == "number":
        return NumberHistogramConfig.from_dict(config)
    if hist_type == "categorical":
        return CategoricalHistogramConfig.from_dict(config)
    if hist_type == "null":
        return NullHistogramConfig.from_dict(config)

    return NullHistogramConfig(f"Invalid histogram configuration {config}")


def create_histogram_from_config(
    config: Union[
        NumberHistogramConfig, CategoricalHistogramConfig,
        NullHistogramConfig, None
    ], **kwargs: Any
) -> Union[NumberHistogram, CategoricalHistogram, NullHistogram]:
    if config is None:
        score_type = kwargs.get("score_type")
        if score_type in ["int", "float"]:
            min_max = kwargs.get("min_max")
            if min_max is not None and min_max.min is not None and \
                    min_max.max is not None:
                return NumberHistogram(
                    NumberHistogramConfig.default_config(min_max)
                )
        if score_type == "str":
            return CategoricalHistogram(
                CategoricalHistogramConfig.default_config()
            )
        return NullHistogram(NullHistogramConfig(
            "No histogram configured and no default config available for type"
            f"{score_type}"
        ))

    hist_type = None
    try:
        if isinstance(config, NumberHistogramConfig):
            hist_type = "number"
            return NumberHistogram(
                config
            )
        if isinstance(config, CategoricalHistogramConfig):
            hist_type = "categorical"
            return CategoricalHistogram(
                config
            )
        if isinstance(config, NullHistogramConfig):
            hist_type = "null"
            return NullHistogram(
                config
            )
        return NullHistogram(NullHistogramConfig(
            "Could not match histogram config type"
        ))
    except BaseException:  # pylint: disable=broad-except
        score_id = kwargs.get("score_id", "")
        logger.exception(
            "Failed to load histogram for score %s",
            score_id
        )
        return NullHistogram(NullHistogramConfig(
            f"Failed to create {hist_type} histogram from config."
        ))


def load_histogram(  # pylint: disable=too-many-return-statements
    config: Union[
        NumberHistogramConfig, CategoricalHistogramConfig,
        NullHistogramConfig, None
    ], resource: GenomicResource, filename: str
) -> Union[NumberHistogram, CategoricalHistogram, NullHistogram]:
    """
    Try and load and return a histogram in a resource.

    On an error or missing histogram, an appropriate NullHistogram is returned.
    """
    if config is None:
        return NullHistogram(NullHistogramConfig("No histogram configured"))

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
