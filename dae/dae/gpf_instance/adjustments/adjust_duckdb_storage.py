import argparse
import logging

from dae.duckdb_storage.duckdb_storage_config import (
    parse_duckdb_config,
)
from dae.gpf_instance.adjustments.adjust_command import AdjustmentsCommand

logger = logging.getLogger(__name__)


class AdjustDuckDbStorageCommand(AdjustmentsCommand):
    """Adjusts impala storage."""

    def __init__(
        self, instance_dir: str, storage_id: str,
        **adjustments: str | bool,
    ) -> None:
        super().__init__(instance_dir)
        self.storage_id = storage_id
        self.adjustments = adjustments

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

        storage_config = parse_duckdb_config(storage).model_dump()

        for key, value in self.adjustments.items():
            if key not in storage_config:
                continue
            if key == "storage_id":
                if value != self.storage_id:
                    logger.error(
                        "storage id (%s) does not match "
                        "storage id in config (%s)",
                        value, self.storage_id)
                    raise ValueError(
                        f"storage id ({value}) does not match "
                        f"storage id in config ({self.storage_id})")
                continue
            if key == "storage_type":
                if value != storage_config["storage_type"]:
                    logger.error(
                        "storage type (%s) does not match "
                        "storage type in config (%s)",
                        value, storage_config["storage_type"])
                    raise ValueError(
                        f"storage type ({value}) does not match "
                        f"storage type in config "
                        f"({storage_config['storage_type']})")
                continue
            if value is None:
                continue
            if isinstance(value, str):
                value = value.strip()
            if value == "":
                continue
            storage[key] = value
        parse_duckdb_config(storage)

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
        parser.add_argument(
            "--memory-limit",
            type=str,
            help="Set memory limit",
        )
        parser.add_argument(
            "--db",
            type=str,
            help="Set duckdb database file",
        )
        parser.add_argument(
            "--bucket-url",
            type=str,
            help="Set S3 bucket URL",
        )
        parser.add_argument(
            "--endpoint-url",
            type=str,
            help="Set S3 endpoint URL",
        )
        parser.add_argument(
            "--base-dir",
            type=str,
            help="Set base directory",
        )
