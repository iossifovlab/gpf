import abc

import duckdb


class DuckDbConnectionFactory(abc.ABC):
    """Abstract factory for DuckDb connection."""

    @abc.abstractmethod
    def connect(self) -> duckdb.DuckDBPyConnection:
        """Create a new DuckDb connection."""
