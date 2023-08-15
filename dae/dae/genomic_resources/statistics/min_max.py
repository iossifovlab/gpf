from __future__ import annotations

from typing import cast, Optional

import yaml
import numpy as np

from dae.genomic_resources.statistics.base_statistic import Statistic


class MinMaxValue(Statistic):
    """Statistic that calculates Min and Max values in a genomic score."""

    def __init__(
            self, score_id: str,
            min_value: float = np.nan, max_value: float = np.nan):
        super().__init__("min_max", "Calculates Min and Max values")
        self.score_id = score_id
        self.min = min_value
        self.max = max_value

    def add_value(self, value: Optional[float]) -> None:
        if value is None:
            return
        self.min = min(value, self.min)
        self.max = max(value, self.max)

    def merge(self, other: MinMaxValue) -> None:
        if not isinstance(other, MinMaxValue):
            raise ValueError()
        if self.score_id != other.score_id:
            raise ValueError(
                "Attempting to merge min max values of different scores!"
            )
        self.min = min(self.min, other.min)
        self.max = max(self.max, other.max)

    def serialize(self) -> str:
        return cast(str, yaml.dump(
            {"score_id": self.score_id, "min": self.min, "max": self.max})
        )

    @staticmethod
    def deserialize(data: str) -> MinMaxValue:
        res = yaml.load(data, yaml.Loader)
        return MinMaxValue(res["score_id"], res["min"], res["max"])


class MinMaxValueStatisticMixin:

    @staticmethod
    def get_min_max_file(score_id: str) -> str:
        return f"min_max_{score_id}.yaml"
