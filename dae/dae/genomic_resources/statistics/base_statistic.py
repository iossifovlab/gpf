from __future__ import annotations
from abc import abstractmethod


class Statistic:
    """
    Base class genomic resource statistics.

    Statistics are generated using task graphs and aggregate values from
    a large amount of data. Each statistic should have a clearly defined
    single unit of data to process (for example, a nucleotide in a
    reference genome).
    """

    statistic_id: str
    description: str

    def __init__(self, statistic_id, description):
        self.statistic_id = statistic_id
        self.description = description

    @abstractmethod
    def add_value(self, value):
        """Add a value to the statistic."""
        raise NotImplementedError()

    def finish(self):
        """
        Perform final calculations for the statistic.

        This step is optional.

        This is called when resource iteration is complete.

        Can also be used when creating more complex resources via
        deserialization.
        """
        return

    @abstractmethod
    def merge(self, other) -> None:
        """Merge the values from another statistic in place."""
        raise NotImplementedError()

    @abstractmethod
    def serialize(self) -> str:
        """Return a serialized version of this statistic."""
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def deserialize(data) -> Statistic:
        """Create a statistic from serialized data."""
        raise NotImplementedError()
