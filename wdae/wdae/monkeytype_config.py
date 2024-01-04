from typing import Iterator

from contextlib import contextmanager

from monkeytype.config import DefaultConfig


class MyConfig(DefaultConfig):
    """Configuration to support monkeytype in wdae Django."""

    @contextmanager
    def cli_context(
        self, command: str
    ) -> Iterator[None]:
        # pylint: disable=import-outside-toplevel
        import django
        django.setup()
        yield


CONFIG = MyConfig()
