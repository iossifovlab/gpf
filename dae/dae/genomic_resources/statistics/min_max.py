from __future__ import annotations

from typing import cast

import numpy as np
import yaml

from dae.genomic_resources.statistics.base_statistic import Statistic


class MinMaxValue(Statistic):
    """Statistic that calculates Min and Max values in a genomic score."""

    def __init__(
        self,
        score_id: str,
        min_value: float = np.nan,
        max_value: float = np.nan,
        count: int = 0,
    ):
        super().__init__("min_max", "Calculates Min and Max values")
        self.score_id = score_id
        self.min = min_value
        self.max = max_value
        self.count = count

    def add_value(self, value: float | None) -> None:
        if value is None:
            return
        self.min = min(value, self.min)
        self.max = max(value, self.max)

    def merge(self, other: Statistic) -> None:
        if not isinstance(other, MinMaxValue):
            raise TypeError("unexpected type of statistics to merge with")
        if self.score_id != other.score_id:
            raise ValueError(
                "Attempting to merge min max values of different scores!",
            )
        if np.isnan(self.min):
            self.min = min(other.min, self.min)
        else:
            self.min = min(self.min, other.min)
        if np.isnan(self.max):
            self.max = max(other.max, self.max)
        else:
            self.max = max(self.max, other.max)
        self.count += other.count

    def add_count(self, count: int = 1) -> None:
        self.count += count

    def serialize(self) -> str:
        serialized = {
            "score_id": self.score_id,
            "min": self.min,
            "max": self.max,
        }
        if self.count != 0:
            serialized["count"] = self.count
        return cast(str, yaml.dump(serialized))

    @staticmethod
    def deserialize(content: str) -> MinMaxValue:
        data = yaml.safe_load(content)
        return MinMaxValue(
            data["score_id"],
            data["min"],
            data["max"],
            data["count"],
        )


class MinMaxValueStatisticMixin:

    @staticmethod
    def get_min_max_file(score_id: str) -> str:
        return f"min_max_{score_id}.yaml"
