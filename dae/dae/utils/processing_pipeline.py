from __future__ import annotations

import abc
import logging
from collections.abc import Iterable, Sequence
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Any

from dae.utils.regions import Region

logger = logging.getLogger(__name__)


class Filter(AbstractContextManager):
    """Base class for all processing pipeline filters."""

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
        return exc_type is None

    @abc.abstractmethod
    def fetch(self, region: Region | None = None) -> Iterable[Any]:
        ...


class PipelineProcessor(AbstractContextManager):
    """A processor that can be used to process variants in a pipeline."""

    def __init__(self, source: Source, filters: Sequence[Filter]) -> None:
        self.source = source
        self.filters = filters

    def __enter__(self) -> PipelineProcessor:
        self.source.__enter__()
        for variant_filter in self.filters:
            variant_filter.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.source.__exit__(exc_type, exc_value, exc_tb)
        for variant_filter in self.filters:
            variant_filter.__exit__(exc_type, exc_value, exc_tb)

        return exc_type is None

    def process_region(self, region: Region | None = None) -> None:
        for data in self.source.fetch(region):
            for _filter in self.filters:
                data = _filter.filter(data)

    def process(self, regions: Iterable[Region] | None = None) -> None:
        """Process a pipeline in batches for the given regions."""
        if regions is None:
            self.process_region(None)
            return
        for region in regions:
            self.process_region(region)
