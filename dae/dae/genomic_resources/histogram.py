"""Handling of genomic scores statistics.

Currently we support only genomic scores histograms.
"""
from __future__ import annotations
from dataclasses import dataclass

import logging
from typing import cast, Optional

import yaml
import numpy as np

from dae.genomic_resources.statistics.base_statistic import Statistic

logger = logging.getLogger(__name__)


@dataclass
class NumberHistogramConfig:
    """Configuration class for number histograms."""

    view_range: tuple[int, int]
    number_of_bins: int = 30
    x_log_scale: bool = False
    y_log_scale: bool = False
    x_min_log: Optional[float] = None

    def to_dict(self):
        return {
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
    def convert_legacy_config(config):
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
    def from_yaml(parsed):
        """Build a number histogram config from a parsed yaml file."""
        yaml_range = parsed.get("view_range", {})
        limits = np.iinfo(np.int64)
        x_min = yaml_range.get("min", limits.min)
        x_max = yaml_range.get("max", limits.max)
        view_range = (x_min, x_max)
        number_of_bins = parsed.get("number_of_bins", 30)
        x_log_scale = parsed.get("x_log_scale", False)
        y_log_scale = parsed.get("y_log_scale", False)
        x_min_log = parsed.get("x_min_log", None)
        return NumberHistogramConfig(
            view_range, number_of_bins,
            x_log_scale, y_log_scale,
            x_min_log
        )


@dataclass
class CategoricalHistogramConfig:
    value_order = Optional[list[str]]
    y_log_scale: bool = False
    x_min_log: Optional[float] = None


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

    @staticmethod
    def default_config(score_id: str):
        return {
            "score": score_id,
            "bins": 100,
        }

    def merge(self, other: NumberHistogram) -> None:
        """Merge two histograms."""
        assert self.config == other.config
        assert all(self.bins == other.bins)

        self.bars += other.bars
        self.out_of_range_values.extend(other.out_of_range_values)

    @property
    def range(self):
        return self.config.view_range

    def add_value(self, value):
        """Add value to the histogram."""
        if value is None:
            return False
        if value < self.config.view_range[0] or \
                value > self.config.view_range[1]:
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

    def serialize(self) -> str:
        return cast(str, yaml.dump(
            {
                "config": self.config.to_dict(),
                "bins": self.bins.tolist(),
                "bars": self.bars.tolist()
            }
        ))

    def plot(self, outfile, score_id):
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
    def deserialize(data) -> NumberHistogram:
        res = yaml.load(data, yaml.Loader)
        # TODO: Remove this
        legacy_keys = set(["x_scale", "y_scale", "bins", "min", "max"])
        if len(legacy_keys.intersection(set(res.get("config").keys()))):
            config = NumberHistogramConfig.convert_legacy_config(
                res.get("config")
            )
        else:
            config = NumberHistogramConfig.from_yaml(res.get("config"))
        return NumberHistogram(
            config,
            bins=np.array(res.get("bins")),
            bars=np.array(res.get("bars"))
        )


class HistogramStatisticMixin:
    """Mixin for creating statistics classes with histograms."""

    @staticmethod
    def get_histogram_file(score_id):
        return f"histogram_{score_id}.yaml"

    @staticmethod
    def get_histogram_image_file(score_id):
        return f"histogram_{score_id}.png"
