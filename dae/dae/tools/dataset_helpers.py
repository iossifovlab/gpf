import glob
import logging
import os
import shutil
from typing import Any, cast

import toml
from box import Box

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance.gpf_instance import GPFInstance

logger = logging.getLogger(__name__)


class DatasetHelpers:
    """Helper class for work with studies in impala genotype storage."""

    def __init__(self, gpf_instance: GPFInstance | None = None) -> None:
        if gpf_instance is None:
            self.gpf_instance = GPFInstance.build()
        else:
            self.gpf_instance = gpf_instance

    def find_genotype_data_config_file(
        self, dataset_id: str,
    ) -> str | None:
        """Find and return config filename for a dataset."""
        config = self.gpf_instance.get_genotype_data_config(dataset_id)
        if config is None:
            self.gpf_instance.reload()
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

    def find_genotype_data_config(self, dataset_id: str) -> Box | None:
        """Find and return configuration of a dataset."""
        config_file = self.find_genotype_data_config_file(dataset_id)
        if config_file is None:
            return None
        with open(config_file, "r") as infile:
            short_config = toml.load(infile)
            return Box(short_config)

    def get_genotype_storage(self, dataset_id: str) -> GenotypeStorage | None:
        """Find the genotype storage that stores a dataset."""
        config = self.find_genotype_data_config(dataset_id)
        if config is None:
            return None
        gpf_instance = self.gpf_instance
        return cast(
            GenotypeStorage | None,
            gpf_instance
            .genotype_storages
            .get_genotype_storage(
                config.genotype_storage.id))

    def rename_study_config(
        self, dataset_id: str, new_id: str,
        config_content: dict[str, Any], *,
        dry_run: bool | None = None,
    ) -> None:
        """Rename study config for a dataset."""
        config_file = self.find_genotype_data_config_file(dataset_id)
        if config_file is None:
            return

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

    def remove_study_config(self, dataset_id: str) -> None:
        """Remove study config for a dataset."""
        config_file = self.find_genotype_data_config_file(dataset_id)
        if config_file is None:
            logger.warning("config file for dataset %s not found", dataset_id)
            return

        config_dir = os.path.dirname(config_file)
        shutil.rmtree(config_dir)

    def disable_study_config(
        self, dataset_id: str, *,
        dry_run: bool | None = None,
    ) -> None:
        """Disable dataset."""
        config_file = self.find_genotype_data_config_file(dataset_id)
        if config_file is None:
            logger.warning("config file for dataset %s not found", dataset_id)
            return
        config_dir = os.path.dirname(config_file)

        logger.info("going to disable study_config %s", config_file)

        if not dry_run:
            os.rename(config_file, f"{config_file}_bak")
            os.rename(config_dir, f"{config_dir}_bak")
