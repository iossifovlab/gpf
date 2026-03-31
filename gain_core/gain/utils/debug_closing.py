# pylint: disable=W0603
import logging
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Generic, Protocol, TypeVar

logger = logging.getLogger(__name__)


LIVE_CONNECTIONS = 0


class HasClose(Protocol):
    """Protocol for objects that have a close method."""

    def close(self) -> None:
        """Close the object."""


T = TypeVar("T", bound=HasClose)


class closing(AbstractContextManager, Generic[T]):  # pylint: disable=C0103
    """Context to automatically close something at the end of a block.

    Code like this:

        with closing(<module>.open(<arguments>)) as f:
            <block>

    is equivalent to this:

        f = <module>.open(<arguments>)
        try:
            <block>
        finally:
            f.close()

    """

    def __init__(self, thing: T) -> None:
        self.thing = thing

    def __enter__(self) -> T:
        global LIVE_CONNECTIONS

        LIVE_CONNECTIONS += 1
        logger.info(
            "[closing] enter %s; live %s", id(self.thing), LIVE_CONNECTIONS,
        )
        return self.thing

    def __exit__(
        self, exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        global LIVE_CONNECTIONS
        self.thing.close()

        LIVE_CONNECTIONS -= 1
        logger.info(
            "[closing] exit %s; live %s", id(self.thing), LIVE_CONNECTIONS,
        )

    def close(self) -> None:
        self.thing.close()
