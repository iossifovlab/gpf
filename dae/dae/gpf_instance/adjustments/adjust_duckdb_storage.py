import argparse
import logging

from dae.gpf_instance.adjustments.adjust_command import AdjustmentsCommand

logger = logging.getLogger(__name__)


class AdjustDuckDbStorageCommand(AdjustmentsCommand):
    """Adjusts impala storage."""

    def __init__(
        self, instance_dir: str, storage_id: str,
        read_only: str,
    ) -> None:
        super().__init__(instance_dir)
        self.storage_id = storage_id
        self.read_only = bool(read_only)

    def execute(self) -> None:
        storages = self.config["genotype_storage"]["storages"]
        storage = None
        for current in storages:
            if current["id"] == self.storage_id:
                storage = current
                break

        if storage is None:
            logger.error(
                "unable to find storage (%s) in instance at %s",
                self.storage_id, self.instance_dir)
            raise ValueError(f"unable to find storage {self.storage_id}")

        if storage.get("storage_type") not in {"duckdb", "duckdb2"}:
            logger.error(
                "storage %s is not DuckDb", self.storage_id)
            raise ValueError(f"storage {self.storage_id} is not DuckDb")

        storage["read_only"] = self.read_only

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add arguments to parser."""
        parser.add_argument(
            "--storage-id",
            type=str,
            required=True,
            help="DuckDb storage id",
        )
        parser.add_argument(
            "--read-only",
            action="store_true",
            help="Set read only mode",
        )
