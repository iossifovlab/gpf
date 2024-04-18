import glob
import logging
import os
import shutil

import toml
from box import Box

logger = logging.getLogger(__name__)


class DatasetHelpers:
    """Helper class for work with studies in impala genotype storage."""

    def __init__(self, gpf_instance=None):
        if gpf_instance is None:
            # pylint: disable=import-outside-toplevel
            from dae.gpf_instance.gpf_instance import GPFInstance
            self.gpf_instance = GPFInstance.build()
        else:
            self.gpf_instance = gpf_instance

    def find_genotype_data_config_file(self, dataset_id):
        """Find and return config filename for a dataset."""
        config = self.gpf_instance.get_genotype_data_config(dataset_id)
        if config is None:
            # pylint: disable=protected-access
            self.gpf_instance._variants_db.reload()
            config = self.gpf_instance.get_genotype_data_config(dataset_id)
            if config is None:
                return None

        assert config is not None, dataset_id

        conf_dir = config.conf_dir

        result = glob.glob(os.path.join(conf_dir, "*.conf"))
        assert len(result) == 1, \
            f"unexpected number of config files in {conf_dir}"
        config_file = result[0]
        assert os.path.exists(config_file)
        return config_file

    def find_genotype_data_config(self, dataset_id):
        """Find and return configuration of a dataset."""
        config_file = self.find_genotype_data_config_file(dataset_id)
        if config_file is None:
            return None
        with open(config_file, "r") as infile:
            short_config = toml.load(infile)
            short_config = Box(short_config)
        return short_config

    def get_genotype_storage(self, dataset_id):
        """Find the genotype storage that stores a dataset."""
        config = self.find_genotype_data_config(dataset_id)
        if config is None:
            return None
        gpf_instance = self.gpf_instance
        genotype_storage = gpf_instance \
            .genotype_storages \
            .get_genotype_storage(
                config.genotype_storage.id)
        return genotype_storage

    def rename_study_config(
            self, dataset_id, new_id, config_content, dry_run=None):
        """Rename study config for a dataset."""
        config_file = self.find_genotype_data_config_file(dataset_id)
        logger.info("going to disable config file %s", config_file)
        if not dry_run:
            os.rename(config_file, f"{config_file}_bak")

        config_dirname = os.path.dirname(config_file)
        new_dirname = os.path.join(os.path.dirname(config_dirname), new_id)
        logger.info(
            "going to rename config directory %s to %s",
            config_dirname, new_dirname)
        if not dry_run:
            os.rename(config_dirname, new_dirname)

        new_config_file = os.path.join(new_dirname, f"{new_id}.conf")

        logger.info("going to create a new config file %s", new_config_file)
        if not dry_run:
            with open(new_config_file, "wt") as outfile:
                content = toml.dumps(config_content)
                outfile.write(content)

    def remove_study_config(self, dataset_id):
        config_file = self.find_genotype_data_config_file(dataset_id)
        config_dir = os.path.dirname(config_file)

        shutil.rmtree(config_dir)

    def disable_study_config(self, dataset_id, dry_run=None):
        """Disable dataset."""
        config_file = self.find_genotype_data_config_file(dataset_id)
        config_dir = os.path.dirname(config_file)

        logger.info("going to disable study_config %s", config_file)

        if not dry_run:
            os.rename(config_file, f"{config_file}_bak")
            os.rename(config_dir, f"{config_dir}_bak")
