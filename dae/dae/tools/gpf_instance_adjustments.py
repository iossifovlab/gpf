from __future__ import annotations

import abc
import argparse
import glob
import logging
import os
import sys
from collections.abc import Iterable
from types import TracebackType
from typing import Any, cast

import toml
import yaml

from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("gpf_instance_adjustments")


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
        with open(self.filename, "w", encoding="utf8") as outfile:
            outfile.write(yaml.safe_dump(self.config, sort_keys=False))

    def __enter__(self) -> AdjustmentsCommand:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()


class InstanceIdCommand(AdjustmentsCommand):
    """Adjusts GPF instance ID."""

    def __init__(self, instance_dir: str, instance_id: str) -> None:
        super().__init__(instance_dir)
        self.instance_id = instance_id

    def execute(self) -> None:
        variables = self.config["vars"]
        variables["instance_id"] = self.instance_id
        logger.info(
            "replacing instance id with %s", self.instance_id)


class AdjustImpalaStorageCommand(AdjustmentsCommand):
    """Adjusts impala storage."""

    def __init__(
        self, instance_dir: str, storage_id: str, read_only: bool,
        hdfs_host: str, impala_hosts: list[str],
    ) -> None:
        super().__init__(instance_dir)
        self.storage_id = storage_id
        self.read_only = read_only
        self.hdfs_host = hdfs_host
        self.impala_hosts = impala_hosts

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
        if self.impala_hosts is not None:
            storage["impala"]["hosts"] = self.impala_hosts


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

        if storage.get("storage_type") not in set(["duckdb", "duckdb2"]):
            logger.error(
                "storage %s is not DuckDb", self.storage_id)
            raise ValueError(f"storage {self.storage_id} is not DuckDb")

        storage["read_only"] = self.read_only


class StudyConfigsAdjustmentCommand(AdjustmentsCommand):
    """Command to adjust study configs."""

    def _execute_studies(self, config_format: str = "toml") -> None:
        study_configs_dir = os.path.join(self.instance_dir, "studies")
        if config_format == "toml":
            pattern = os.path.join(study_configs_dir, "**/*.conf")
        elif config_format == "yaml":
            pattern = os.path.join(study_configs_dir, "**/*.yaml")

        config_filenames = glob.glob(pattern, recursive=True)

        for config_filename in config_filenames:
            logger.info("processing study %s", config_filename)
            with open(config_filename, "rt", encoding="utf8") as infile:
                if config_format == "toml":
                    study_config = toml.loads(infile.read())
                elif config_format == "yaml":
                    study_config = yaml.safe_load(infile.read())

            study_id = study_config["id"]

            result_config = self.adjust_study(
                study_id, cast(dict[str, Any], study_config))

            with open(config_filename, "w", encoding="utf8") as outfile:
                if config_format == "toml":
                    outfile.write(toml.dumps(result_config))
                elif config_format == "yaml":
                    outfile.write(
                        yaml.safe_dump(result_config, sort_keys=False))

    def _execute_datasets(self, config_format: str = "toml") -> None:
        study_configs_dir = os.path.join(self.instance_dir, "datasets")
        if config_format == "toml":
            pattern = os.path.join(study_configs_dir, "**/*.conf")
        elif config_format == "yaml":
            pattern = os.path.join(study_configs_dir, "**/*.yaml")
        config_filenames = glob.glob(pattern, recursive=True)

        for config_filename in config_filenames:
            logger.info("processing study %s", config_filename)
            with open(config_filename, "rt", encoding="utf8") as infile:
                if config_format == "toml":
                    dataset_config = toml.loads(infile.read())
                elif config_format == "yaml":
                    dataset_config = yaml.safe_load(infile.read())

            dataset_id = dataset_config["id"]
            result_config = self.adjust_dataset(
                dataset_id, cast(dict[str, Any], dataset_config))

            with open(config_filename, "w", encoding="utf8") as outfile:
                if config_format == "toml":
                    outfile.write(toml.dumps(result_config))
                elif config_format == "yaml":
                    outfile.write(
                        yaml.safe_dump(result_config, sort_keys=False))

    def adjust_study(
        self, _study_id: str,
        study_config: dict[str, Any],
    ) -> dict[str, Any]:
        return study_config

    def adjust_dataset(
        self, _dataset_id: str, dataset_config: dict[str, Any],
    ) -> dict[str, Any]:
        return dataset_config


class DefaultGenotypeStorage(StudyConfigsAdjustmentCommand):
    """Adjust default genotype storage."""

    def __init__(self, instance_dir: str, storage_id: str) -> None:
        super().__init__(instance_dir)
        self.storage_id = storage_id

    def execute(self) -> None:
        genotype_storage_config = self.config["genotype_storage"]
        default_storage = genotype_storage_config["default"]
        storages = genotype_storage_config["storages"]
        storage_ids = set(map(lambda s: s["id"], storages))

        if default_storage not in storage_ids:
            logger.error(
                "GPF instance misconfigured; "
                "current default genotype storage %s not found "
                "in the list of storages: %s",
                default_storage, storage_ids)
            raise ValueError(default_storage)
        if self.storage_id not in storage_ids:
            logger.error(
                "bad storage for GPF instance; "
                "passed genotype storage %s not found "
                "in the list of configured storages: %s",
                default_storage, storage_ids)
            raise ValueError(default_storage)

        genotype_storage_config["default"] = self.storage_id
        logger.info(
            "replacing default storage id with %s", self.storage_id)

        self._execute_studies()

    def adjust_study(
        self, _study_id: str,
        study_config: dict[str, Any],
    ) -> dict[str, Any]:
        genotype_storage = study_config.get("genotype_storage")
        if genotype_storage is not None and \
                genotype_storage.get("id") is None:
            genotype_storage["id"] = self.storage_id
        return study_config


class EnableDisableStudies(StudyConfigsAdjustmentCommand):
    """Enable or disable collection of studies."""

    def __init__(
        self, instance_dir: str,
        study_ids: Iterable[str],
        enabled: bool = False,
    ) -> None:
        super().__init__(instance_dir)
        self.study_ids = study_ids
        self.enabled = enabled

    def _msg(self) -> str:
        msg = "disable"
        if self.enabled:
            msg = "enable"
        return msg

    def execute(self) -> None:
        logger.info(
            "going to %s following studies: %s", self._msg(), self.study_ids)
        self._execute_studies(config_format="toml")
        self._execute_studies(config_format="yaml")
        self._execute_datasets(config_format="toml")
        self._execute_datasets(config_format="yaml")

        gpfjs = self.config.get("gpfjs")
        if gpfjs is not None:
            visible_datasets = gpfjs.get("visible_datasets")
            if visible_datasets:
                if self.enabled:
                    result = visible_datasets
                    for study_id in self.study_ids:
                        if study_id not in result:
                            result.append(study_id)
                else:
                    result = []
                    for study_id in visible_datasets:
                        if study_id in self.study_ids:
                            continue
                        result.append(study_id)

                gpfjs["visible_datasets"] = result

    def adjust_study(
        self, study_id: str,
        study_config: dict[str, Any],
    ) -> dict[str, Any]:
        if study_id in self.study_ids:
            logger.info("study %s %s", study_id, self._msg())
            study_config["enabled"] = self.enabled
        return study_config

    def adjust_dataset(
        self, dataset_id: str,
        dataset_config: dict[str, Any],
    ) -> dict[str, Any]:
        if dataset_id in self.study_ids:
            logger.info("dataset %s %s", dataset_id, self._msg())
            dataset_config["enabled"] = self.enabled
        studies = dataset_config["studies"]
        result = []
        for study_id in studies:
            if study_id in self.study_ids:
                logger.info(
                    "removing %s from dataset %s", study_id, dataset_id)
                continue
            result.append(study_id)
        dataset_config["studies"] = result

        return dataset_config


def cli(argv: list[str] | None = None) -> None:
    """Handle cli invocation."""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="adjustments in GPF instance configuration")
    VerbosityConfiguration.set_arguments(parser)
    parser.add_argument("-i", "--instance", type=str, default=None)

    subparsers = parser.add_subparsers(dest="command",
                                       help="Command to execute")

    parser_instance_id = subparsers.add_parser(
        "id", help="change the GPF instance ID")
    parser_instance_id.add_argument(
        "instance_id", type=str,
        help="new GPF instance ID")

    parser_impala_storage = subparsers.add_parser(
        "impala-storage", help="adjust the GPF instance impala storage")
    parser_impala_storage.add_argument(
        "storage_id", type=str,
        help="impala storage ID")
    parser_impala_storage.add_argument(
        "--read-only", type=str, default="true",
        help="read-only flag for impala storage")
    parser_impala_storage.add_argument(
        "--impala-hosts", type=str, nargs="+",
        help="list of impala hosts")
    parser_impala_storage.add_argument(
        "--hdfs-host", type=str,
        help="HDFS host")

    parser_duckdb_storage = subparsers.add_parser(
        "duckdb-storage", help="adjust the GPF instance DuckDb storage")
    parser_duckdb_storage.add_argument(
        "storage_id", type=str,
        help="DuckDb storage ID")
    parser_duckdb_storage.add_argument(
        "--read-only", type=str, default="true",
        help="DuckDb storage read only flag")

    parser_genotype_storage = subparsers.add_parser(
        "storage", help="change the GPF default genotype storage")
    parser_genotype_storage.add_argument(
        "storage_id", type=str,
        help="new GPF default genotype storage")

    parser_disable_studies = subparsers.add_parser(
        "disable-studies", help="disable studies from GPF instance")
    parser_disable_studies.add_argument(
        "study_id", type=str, nargs="+",
        help="study IDs to disable")

    parser_enable_studies = subparsers.add_parser(
        "enable-studies", help="enable studies from GPF instance")
    parser_enable_studies.add_argument(
        "study_id", type=str, nargs="+",
        help="study IDs to enable")

    args = parser.parse_args(argv)

    instance_dir = args.instance
    if instance_dir is None:
        instance_dir = os.environ.get("DAE_DB_DIR")
    if instance_dir is None:
        logger.error("can't identify GPF instance to work with")
        sys.exit(1)

    VerbosityConfiguration.set(args)

    if args.command == "id":
        with InstanceIdCommand(instance_dir, args.instance_id) as cmd:
            cmd.execute()

    elif args.command == "impala-storage":
        read_only = args.read_only.lower() != "false"
        with AdjustImpalaStorageCommand(
                instance_dir, args.storage_id, read_only,
                args.hdfs_host, args.impala_hosts) as cmd:
            cmd.execute()

    elif args.command == "storage":
        with DefaultGenotypeStorage(instance_dir, args.storage_id) as cmd:
            cmd.execute()

    elif args.command == "duckdb-storage":
        with AdjustDuckDbStorageCommand(
                instance_dir, args.storage_id, args.read_only) as cmd:
            cmd.execute()

    elif args.command == "disable-studies":
        with EnableDisableStudies(
                instance_dir, set(args.study_id), enabled=False) as cmd:
            cmd.execute()

    elif args.command == "enable-studies":
        with EnableDisableStudies(
                instance_dir, set(args.study_id), enabled=True) as cmd:
            cmd.execute()
