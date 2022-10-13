from multiprocessing.sharedctypes import Value
import os
import sys
import logging
import argparse
import glob
import abc

import yaml
import toml


logger = logging.getLogger("gpf_instance_adjustments")


class VerbosityConfiguration:
    @staticmethod
    def set_argumnets(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--verbose", "-v", "-V", action="count", default=0)

    @staticmethod
    def set(args):
        if args.verbose == 1:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose >= 2:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)


class AdjustmentsCommand(abc.ABC):
    """Abstract class for adjusting an GPF instance config."""
    def __init__(self, instance_dir):
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
    def execute(self):
        """Executes adjustment command."""
        pass

    def close(self):
        """Saves adjusted config."""
        with open(self.filename, "w", encoding="utf8") as outfile:
            outfile.write(yaml.safe_dump(self.config))

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()


class InstanceIdCommand(AdjustmentsCommand):
    """Adjusts GPF instance ID."""
    def __init__(self, instance_dir, instance_id):
        super().__init__(instance_dir)
        self.instance_id = instance_id

    def execute(self):
        variables = self.config["vars"]
        variables["instance_id"] = self.instance_id
        logger.info(
            "replacing instance id with %s", self.instance_id)


class AdjustImpalaStorageCommand(AdjustmentsCommand):
    """Adjusts impala storage."""
    def __init__(self, instance_dir, storage_id, hdfs_host, impala_hosts):
        super().__init__(instance_dir)
        self.storage_id = storage_id
        self.hdfs_host = hdfs_host
        self.impala_hosts = impala_hosts

    def execute(self):
        storages = self.config["storage"]
        storage = storages.get(self.storage_id)
        if storage is None:
            logger.error(
                "unable to find storage (%s) in instance at %s",
                self.storage_id, self.instance_dir)
            raise ValueError(f"unable to find storage {self.storage_id}")

        if storage.get("storage_type") != "impala":
            logger.error(
                "storage %s is not Impala", self.storage_id)
            raise ValueError(f"storage {self.storage_id} is not Impala")

        storage["hdfs"]["host"] = self.hdfs_host
        storage["impala"]["hosts"] = self.impala_hosts


class StudyConfigsAdjustmentCommand(AdjustmentsCommand):

    def __init__(self, instance_dir):
        super().__init__(instance_dir)

    def _execute_studies(self):
        study_configs_dir = os.path.join(self.instance_dir, "studies")
        pattern = os.path.join(study_configs_dir, "**/*.conf")
        config_filenames = glob.glob(pattern, recursive=True)

        for config_filename in config_filenames:
            logger.info("processing study %s", config_filename)
            with open(config_filename, "rt", encoding="utf8") as infile:
                study_config = toml.loads(infile.read())
            study_id = study_config["id"]

            result_config = self.adjust_study(study_id, study_config)

            with open(config_filename, "w", encoding="utf8") as outfile:
                outfile.write(toml.dumps(result_config))

    def _execute_datasets(self):
        study_configs_dir = os.path.join(self.instance_dir, "datasets")
        pattern = os.path.join(study_configs_dir, "**/*.conf")
        config_filenames = glob.glob(pattern, recursive=True)

        for config_filename in config_filenames:
            logger.info("processing study %s", config_filename)
            with open(config_filename, "rt", encoding="utf8") as infile:
                dataset_config = toml.loads(infile.read())
            dataset_id = dataset_config["id"]

            result_config = self.adjust_dataset(dataset_id, dataset_config)

            with open(config_filename, "w", encoding="utf8") as outfile:
                outfile.write(toml.dumps(result_config))

    def adjust_study(self, study_id, study_config):
        return study_config

    def adjust_dataset(self, dataset_id, dataset_config):
        return dataset_config


class DefaultGenotypeStorage(StudyConfigsAdjustmentCommand):

    def __init__(self, instance_dir, storage_id):
        super().__init__(instance_dir)
        self.storage_id = storage_id

    def execute(self):
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

    def adjust_study(self, study_id, study_config):
        genotype_storage = study_config.get("genotype_storage")
        if genotype_storage is not None and \
                genotype_storage.get("id") is None:
            genotype_storage["id"] = self.storage_id
        return study_config


class EnableDisableStudies(StudyConfigsAdjustmentCommand):

    def __init__(self, instance_dir, study_ids, enabled=False):
        super().__init__(instance_dir)
        self.study_ids = study_ids
        self.enabled = enabled

    def execute(self):
        logger.info("going to disable following studies: %s", self.study_ids)
        self._execute_studies()
        self._execute_datasets()

        gpfjs = self.config.get("gpfjs")
        if gpfjs is not None:
            selected_genotype_data = gpfjs.get("selected_genotype_data")
            if selected_genotype_data:
                result = []
                for study_id in selected_genotype_data:
                    if study_id in self.study_ids:
                        continue
                    result.append(study_id)
                gpfjs["selected_genotype_data"] = result

    def adjust_study(self, study_id, study_config):
        if study_id in self.study_ids:
            logger.info("study %s disabled", study_id)
            study_config["enabled"] = self.enabled
        return study_config

    def adjust_dataset(self, dataset_id, dataset_config):
        if dataset_id in self.study_ids:
            logger.info("dataset %s disabled", dataset_id)
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


def cli(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(
        description="adjustments in GPF instance configuration")
    VerbosityConfiguration.set_argumnets(parser)
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
        "--impala-hosts", type=str, nargs="+",
        help="list of impala hosts")
    parser_impala_storage.add_argument(
        "--hdfs-host", type=str,
        help="HDFS host")

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
        with AdjustImpalaStorageCommand(
                instance_dir, args.storage_id,
                args.hdfs_host, args.impala_hosts) as cmd:
            cmd.execute()

    elif args.command == "storage":
        with DefaultGenotypeStorage(instance_dir, args.storage_id) as cmd:
            cmd.execute()

    elif args.command == "disable-studies":
        with EnableDisableStudies(
                instance_dir, set(args.study_id), enabled=False) as cmd:
            cmd.execute()

    elif args.command == "enable-studies":
        with EnableDisableStudies(
                instance_dir, set(args.study_id), enabled=True) as cmd:
            cmd.execute()
