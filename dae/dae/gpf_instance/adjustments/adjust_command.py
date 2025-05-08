from __future__ import annotations

import abc
import logging
import os
import pathlib
from types import TracebackType

import yaml

logger = logging.getLogger(__name__)


class AdjustmentsCommand(abc.ABC):
    """Abstract class for adjusting an GPF instance config."""

    def __init__(self, instance_dir: str) -> None:
        self.instance_dir = instance_dir
        self.filename = os.path.join(instance_dir, "gpf_instance.yaml")
        if not os.path.exists(self.filename):
            logger.error(
                "%s is not a GPF instance; "
                "gpf_instance.yaml (%s) not found",
                instance_dir, self.filename)
            raise ValueError(instance_dir)

        with open(self.filename, "rt", encoding="utf8") as infile:
            self.config = yaml.safe_load(infile.read())

    @abc.abstractmethod
    def execute(self) -> None:
        """Execute adjustment command."""

    def close(self) -> None:
        """Save adjusted config."""
        pathlib.Path(self.filename).write_text(
            yaml.safe_dump(self.config, sort_keys=False),
            encoding="utf8",
        )

    def __enter__(self) -> AdjustmentsCommand:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
