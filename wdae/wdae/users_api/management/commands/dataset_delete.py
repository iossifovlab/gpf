import logging


from django.core.management.base import BaseCommand

from gpf_instance.gpf_instance import get_wgpf_instance
from .dataset_mixin import DatasetBaseMixin


logger = logging.getLogger(__name__)


class Command(BaseCommand, DatasetBaseMixin):
    """Delete a dataset."""

    help = "Rename an existing dataset"

    def add_arguments(self, parser):
        parser.add_argument("dataset", type=str)

    def handle(self, *args, **options):
        assert "dataset" in options and options["dataset"] is not None

        dataset_id = options["dataset"]
        dataset_id = dataset_id.strip()
        dataset = self.get_dataset(dataset_id)
        assert dataset is not None, \
            f"dataset {dataset_id} should exists"

        logger.debug("dataset found: %s", dataset.dataset_id)

        config = get_wgpf_instance().get_genotype_data_config(dataset_id)
        assert config is not None

        genotype_data = get_wgpf_instance().get_genotype_data(dataset_id)

        if genotype_data.is_group:
            self.remove_study_config(dataset_id)
            self.remove_wdae_dataset_and_groups(dataset_id)

        else:
            assert self.is_impala_genotype_storage(dataset_id), \
                f"genotype storage {config.genotype_storage.id} is not Impala"

            self.remove_study_config(dataset_id)
            self.remove_wdae_dataset_and_groups(dataset_id)

            self.dataset_drop_impala_tables(config)
            self.dataset_remove_hdfs_directory(config)
