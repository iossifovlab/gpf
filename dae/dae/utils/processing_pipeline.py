import abc
from contextlib import AbstractContextManager
from typing import Any


class Filter(AbstractContextManager):
    @abc.abstractmethod
    def filter(self, data: Any) -> Any:
        ...
