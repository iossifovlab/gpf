import logging

from django.core.management.base import BaseCommand

from gpf_instance.gpf_instance import get_wgpf_instance

from .dataset_mixin import DatasetBaseMixin

logger = logging.getLogger(__name__)


class Command(BaseCommand, DatasetBaseMixin):
    """Check dataset HDFS directories."""

    help = "Check an existing dataset"

    def add_arguments(self, parser):
        parser.add_argument("dataset", type=str)

    def handle(self, *args, **options):
        assert "dataset" in options and options["dataset"] is not None

        dataset_id = options["dataset"]
        dataset_id = dataset_id.strip()
        dataset = self.get_dataset(dataset_id)
        assert dataset is not None

        logger.debug("dataset found: %s", dataset.dataset_id)

        assert dataset is not None

        config = get_wgpf_instance().get_genotype_data_config(dataset_id)
        assert config is not None

        genotype_data = get_wgpf_instance().get_genotype_data(dataset_id)
        print(type(genotype_data), genotype_data)

        if genotype_data.is_group:
            pass
        else:
            assert self.is_impala_genotype_storage(config), \
                f"genotype storage {config.genotype_storage.id} is not Impala"

            self.check_dataset_hdfs_directories(config, dataset_id)
            self.check_dataset_impala_tables(config)
