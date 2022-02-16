import yaml
import os
import sys
import logging
import argparse
import glob
import toml
import pprint


logger = logging.getLogger("gpf_instance_adjustments")


class VerbosityConfiguration:
    @staticmethod
    def set_argumnets(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--verbose', '-v', '-V', action='count', default=0)

    @staticmethod
    def set(args):
        if args.verbose == 1:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose >= 2:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)


class AdjustmentsCommand:

    def __init__(self, instance_dir):
        self.instance_dir = instance_dir
        self.filename = os.path.join(instance_dir, "gpf_instance.yaml")
        if not os.path.exists(self.filename):
            logger.error(
                f"{instance_dir} is not a GPF instance; "
                f"gpf_instance.yaml ({self.filename}) not found")
            raise ValueError(instance_dir)

        with open(self.filename) as infile:
            self.config = yaml.safe_load(infile.read())

    def execute(self):
        pass

    def close(self):
        with open(self.filename, "w") as outfile:
            outfile.write(yaml.safe_dump(self.config))

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()


class InstanceIdCommand(AdjustmentsCommand):

    def __init__(self, instance_dir, instance_id):
        super().__init__(instance_dir)
        self.instance_id = instance_id

    def execute(self):
        vars = self.config["vars"]
        vars["instance_id"] = self.instance_id
        logger.info(
            f"replacing instance id with {self.instance_id}")


class StudyConfigsAdjustmentCommand(AdjustmentsCommand):

    def __init__(self, instance_dir):
        super().__init__(instance_dir)

    def _execute_studies(self):
        study_configs_dir = os.path.join(self.instance_dir, "studies")
        pattern = os.path.join(study_configs_dir, "**/*.conf")
        config_filenames = glob.glob(pattern, recursive=True)
    
        for config_filename in config_filenames:
            logger.info(f"processing study {config_filename}")
            with open(config_filename, "rt") as infile:
                study_config = toml.loads(infile.read())
            study_id = study_config["id"]

            result_config = self.adjust_study(study_id, study_config)

            with open(config_filename, "w") as outfile:
                outfile.write(toml.dumps(result_config))

    def _execute_datasets(self):
        study_configs_dir = os.path.join(self.instance_dir, "datasets")
        pattern = os.path.join(study_configs_dir, "**/*.conf")
        config_filenames = glob.glob(pattern, recursive=True)
    
        for config_filename in config_filenames:
            logger.info(f"processing study {config_filename}")
            with open(config_filename, "rt") as infile:
                dataset_config = toml.loads(infile.read())
            dataset_id = dataset_config["id"]

            result_config = self.adjust_dataset(dataset_id, dataset_config)

            with open(config_filename, "w") as outfile:
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
        default_genotype_storage = self.config["genotype_storage"]
        default = default_genotype_storage["default"]

        storages = self.config["storage"]
        if default not in storages:
            logger.error(
                f"GPF instance misconfigured; "
                f"current default genotype storage {default} not found "
                f"in the list of storages: {list(storages.keys())}")
            raise ValueError(default)
        if self.storage_id not in storages:
            logger.error(
                f"bad storage for GPF instance; "
                f"passed genotype storage {default} not found "
                f"in the list of configured storages: {list(storages.keys())}")
            raise ValueError(default)

        default_genotype_storage["default"] = self.storage_id
        logger.info(
            f"replacing default storage id with {self.storage_id}")

        self._execute_studies()

    def adjust_study(self, study_id, study_config):
        genotype_storage = study_config.get("genotype_storage")
        if genotype_storage is not None:
            if genotype_storage.get("id") is not None:
                genotype_storage["id"] = self.storage_id
        return study_config


class DisableStudies(StudyConfigsAdjustmentCommand):

    def __init__(self, instance_dir, study_ids):
        super().__init__(instance_dir)
        self.study_ids = study_ids

    def execute(self):
        logger.info(f"going to disable following studies: {self.study_ids}")
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
            logger.info(f"study {study_id} disabled")
            study_config["enabled"] = False
        return study_config

    def adjust_dataset(self, dataset_id, dataset_config):
        if dataset_id in self.study_ids:
            logger.info(f"dataset {dataset_id} disabled")
            dataset_config["enabled"] = False
        studies = dataset_config["studies"]
        result = []
        for study_id in studies:
            if study_id in self.study_ids:
                logger.info(f"removing {study_id} from dataset {dataset_id}")
                continue
            result.append(study_id)
        dataset_config["studies"] = result

        return dataset_config


def cli(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(
        description="adjustments in GPF instance configuration")
    VerbosityConfiguration.set_argumnets(parser)
    parser.add_argument("-i", "--instance", type=str, default=None)
    

    subparsers = parser.add_subparsers(dest='command',
                                       help='Command to execute')

    parser_instance_id = subparsers.add_parser(
        'id', help='change the GPF instance ID')
    parser_instance_id.add_argument(
        'instance_id', type=str,
        help='new GPF instance ID')

    parser_genotype_storage = subparsers.add_parser(
        'storage', help='change the GPF default genotype storage')
    parser_genotype_storage.add_argument(
        'storage_id', type=str,
        help='new GPF default genotype storage')

    parser_disable_studies = subparsers.add_parser(
        'disable-studies', help='disable studies from GPF instance')
    parser_disable_studies.add_argument(
        'study_id', type=str, nargs="+",
        help='study IDs to disable')

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

    elif args.command == "storage":
        with DefaultGenotypeStorage(instance_dir, args.storage_id) as cmd:
            cmd.execute()

    elif args.command == "disable-studies":
        with DisableStudies(instance_dir, set(args.study_id)) as cmd:
            cmd.execute()
