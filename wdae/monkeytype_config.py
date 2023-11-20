from typing import Iterator

from contextlib import contextmanager

from monkeytype.config import DefaultConfig


class MyConfig(DefaultConfig):

    @contextmanager
    def cli_context(
        self, command: str
    ) -> Iterator[None]:
        import django
        django.setup()
        yield


CONFIG = MyConfig()

