from __future__ import annotations
from typing import cast
import yaml

from dae.genomic_resources.statistics.base_statistic import Statistic


class MinMaxValue(Statistic):
    """Statistic that calculates Min and Max values in a genomic score."""

    def __init__(self, score_id, min_value=None, max_value=None):
        super().__init__("min_max", "Calculates Min and Max values")
        self.score_id = score_id
        self.min = min_value
        self.max = max_value

    def add_record(self, record):
        value = record[self.score_id]
        if value is None:
            return
        self.add_value(value)

    def add_value(self, value):
        if self.min is None or value < self.min:
            self.min = value
        if self.max is None or value > self.max:
            self.max = value

    def merge(self, other: MinMaxValue) -> None:
        if not isinstance(other, MinMaxValue):
            raise ValueError()
        if self.score_id != other.score_id:
            raise ValueError(
                "Attempting to merge min max values of different scores!"
            )
        if self.min is None:
            self.min = other.min
        elif other.min is None:
            pass
        elif other.min < self.min:
            self.min = other.min

        if self.max is None:
            self.max = other.max
        elif other.max is None:
            pass
        elif other.max > self.max:
            self.max = other.max

    def serialize(self) -> str:
        return cast(str, yaml.dump(
            {"score_id": self.score_id, "min": self.min, "max": self.max})
        )

    @staticmethod
    def deserialize(data) -> MinMaxValue:
        res = yaml.load(data, yaml.Loader)
        return MinMaxValue(res["score_id"], res.get("min"), res.get("max"))


class MinMaxValueStatisticMixin:

    @staticmethod
    def get_min_max_file(score_id):
        return f"min_max_{score_id}.yaml"
