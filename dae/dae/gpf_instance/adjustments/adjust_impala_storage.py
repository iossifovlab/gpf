import argparse
import logging
from typing import Any

from dae.gpf_instance.adjustments.adjust_command import AdjustmentsCommand

logger = logging.getLogger(__name__)


class AdjustImpalaStorageCommand(AdjustmentsCommand):
    """Adjusts impala storage."""

    def __init__(
        self, instance_dir: str, storage_id: str, *,
        read_only: bool,
        hdfs_host: str | None = None, hdfs_base_dir: str | None = None,
        impala_hosts: list[str] | None = None,
        impala_db: str | None = None,
        **_kwargs: Any | bool,
    ) -> None:
        super().__init__(instance_dir)
        self.storage_id = storage_id
        self.read_only = read_only
        self.hdfs_host = hdfs_host
        self.hdfs_base_dir = hdfs_base_dir

        self.impala_hosts = impala_hosts
        self.impala_db = impala_db

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

        if storage.get("storage_type") != "impala":
            logger.error(
                "storage %s is not Impala", self.storage_id)
            raise ValueError(f"storage {self.storage_id} is not Impala")

        if self.read_only is not None:
            storage["read_only"] = self.read_only
        if self.hdfs_host is not None:
            storage["hdfs"]["host"] = self.hdfs_host
        if self.hdfs_base_dir is not None:
            storage["hdfs"]["base_dir"] = self.hdfs_base_dir
        if self.impala_hosts is not None:
            storage["impala"]["hosts"] = self.impala_hosts
        if self.impala_db is not None:
            storage["impala"]["db"] = self.impala_db

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add arguments to parser."""

        parser.add_argument(
            "--storage-id", type=str,
            required=True,
            help="impala storage ID")
        parser.add_argument(
            "--read-only",
            action=argparse.BooleanOptionalAction,
            help="read-only flag for impala storage",
        )
        parser.add_argument(
            "--impala-hosts", type=str, nargs="+",
            help="list of impala hosts")
        parser.add_argument(
            "--hdfs-host", type=str,
            help="HDFS host")

        parser.add_argument(
            "--impala-db",
            type=str,
            help="Set Impala database name",
        )
        parser.add_argument(
            "--hdfs-base-dir",
            type=str,
            help="Set HDFS base directory",
        )
