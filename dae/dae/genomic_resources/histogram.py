"""Handling of genomic scores statistics.

Currently we support only genomic scores histograms.
"""
from __future__ import annotations

import logging
from typing import cast

import yaml
import numpy as np

from dae.genomic_resources.statistic import Statistic

logger = logging.getLogger(__name__)


class Histogram(Statistic):
    """Class to represent a histogram."""

    # pylint: disable=too-many-instance-attributes
    # FIXME:
    def __init__(self, config, bins=None, bars=None):
        super().__init__("histogram", "Collects values for histogram.")
        self.config = config
        self.bins = bins
        self.bars = bars

        try:
            self.score_id = self.config["score"]
            self.bins_count = self.config["bins"]
        except KeyError as e:
            raise ValueError(
                f"Invalid histogram configuration, cannot find {e.args[0]}"
            ) from e

        limits = np.iinfo(np.int64)
        self.x_min = self.config.get("min", limits.min)
        self.x_max = self.config.get("max", limits.max)
        self.x_scale = self.config.get("x_scale", "linear")
        self.y_scale = self.config.get("y_scale", "linear")
        self.x_min_log = self.config.get("x_min_log")
        if self.x_scale == "log" and self.x_min_log is None:
            raise ValueError(
                "Invalid histogram configuration, missing x_min_log"
            )

        if self.bins is None and self.bars is None:
            if self.x_scale == "linear":
                self.bins = np.linspace(
                    self.x_min,
                    self.x_max,
                    self.bins_count + 1,
                )
            elif self.x_scale == "log":
                assert self.x_min_log is not None
                self.bins = np.array([
                    self.x_min,
                    * np.logspace(
                        np.log10(self.x_min_log),
                        np.log10(self.x_max),
                        self.bins_count
                    )])
            self.bars = np.zeros(self.bins_count, dtype=np.int64)
        elif self.bins is None or self.bars is None:
            raise ValueError(
                f"Cannot instantiate histogram with only bins or only bars!"
            )

        if self.x_scale not in ("linear", "log"):
            raise ValueError(f"unexpected histogram xscale: {self.x_scale}")

        if self.y_scale not in ("linear", "log"):
            raise ValueError(f"unexpected yscale {self.y_scale}")

    def merge(self, other: Histogram) -> None:
        """Merge two histograms."""
        assert self.x_scale == other.x_scale
        assert self.x_min == other.x_min
        assert self.x_min_log == other.x_min_log
        assert self.x_max == other.x_max
        assert all(self.bins == other.bins)

        self.bars += other.bars

    @property
    def range(self):
        if self.x_min is not None and self.x_max is not None:
            return [self.x_min, self.x_max]
        return None

    def add_record(self, record):
        value = record[self.score_id]
        if value is None:
            return False
        self.add_value(value)

    def add_value(self, value):
        """Add value to the histogram."""
        if value < self.x_min:
            logger.warning(
                "value %s out of range: [%s, %s]; adding to the first bin",
                value, self.x_min, self.x_max)
            self.bars[0] += 1
            return False
        if value > self.x_max:
            logger.warning(
                "value %s out of range: [%s, %s]; adding to the last bin",
                value, self.x_min, self.x_max)
            self.bars[-1] += 1
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
                "config": self.config,
                "bins": self.bins,
                "bars": self.bars
            }
        ))

    @staticmethod
    def deserialize(data) -> Histogram:
        res = yaml.load(data, yaml.Loader)
        return Histogram(
            res.get("config"),
            bins=res.get("bins"),
            bars=res.get("bars")
        )
