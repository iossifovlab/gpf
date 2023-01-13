from __future__ import annotations
from abc import abstractmethod


class Statistic:
    """Base class genomic resource statistics."""

    statistic_id: str
    description: str

    def __init__(self, statistic_id, description):
        self.statistic_id = statistic_id
        self.description = description

    @abstractmethod
    def add_value(self, value):
        pass

    @abstractmethod
    def merge(self, other) -> None:
        pass

    @abstractmethod
    def serialize(self) -> str:
        pass

    @staticmethod
    @abstractmethod
    def deserialize(data) -> Statistic:
        pass
