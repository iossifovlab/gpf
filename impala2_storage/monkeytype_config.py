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
        from django.conf import settings

        settings.configure()
        django.setup()
        yield


CONFIG = MyConfig()
