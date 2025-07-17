import abc
from collections.abc import Iterable
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Any

from dae.utils.regions import Region


class Filter(AbstractContextManager):
    """Base class for all processing pipeline filters."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        return exc_type is not None

    @abc.abstractmethod
    def filter(self, data: Any) -> Any:
        ...


class Source(AbstractContextManager):
    """Base class for all processing pipeline sources."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        return exc_type is not None

    @abc.abstractmethod
    def fetch(self, region: Region | None = None) -> Iterable[Any]:
        ...
