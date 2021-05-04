import logging

from django.core.management.base import BaseCommand

from .dataset_mixin import DatasetBaseMixin


logger = logging.getLogger(__name__)


class Command(BaseCommand, DatasetBaseMixin):
    help = "Rename an existing dataset"

    def __init__(self, **kwargs):
        DatasetBaseMixin.__init__(self)
        BaseCommand.__init__(self, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", "-n", action="store_true")
        parser.add_argument("old_dataset", type=str)
        parser.add_argument("new_dataset", type=str)

    def handle(self, *args, **options):
        assert "old_dataset" in options and options["old_dataset"] is not None
        assert "new_dataset" in options and options["new_dataset"] is not None
        assert "dry_run" in options

        dataset_id = options["old_dataset"]
        dataset_id = dataset_id.strip()
        dataset = self.get_dataset(dataset_id)
        assert dataset is not None, \
            f"dataset {dataset_id} should exists"

        logger.debug(f"dataset found: {dataset.dataset_id}")

        new_id = options["new_dataset"]
        assert self.get_dataset(new_id) is None, \
            f"dataset {new_id} already exists"
        dry_run = options["dry_run"]

        config = self.gpf_instance.get_genotype_data_config(dataset_id)
        assert config is not None

        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)

        if genotype_data.is_group:
            short_config = self.find_dataset_config(dataset_id)
            short_config.id = new_id

            self.rename_study_config(dataset_id, new_id, short_config)
            self.rename_wdae_dataset_and_groups(dataset_id, new_id)

        else:
            assert self.is_impala_genotype_storage(dataset_id), \
                f"genotype storage {config.genotype_storage.id} is not Impala"

            self.dataset_rename_hdfs_directory(
                dataset_id, new_id, dry_run=dry_run)
            pedigree_table, variants_table = \
                self.dataset_recreate_impala_tables(
                    dataset_id, new_id, dry_run=dry_run)

            short_config = self.find_genotype_data_config(dataset_id)

            short_config.id = new_id
            short_config.genotype_storage.tables.pedigree = pedigree_table
            if variants_table:
                short_config.genotype_storage.tables.variants = variants_table

            self.rename_study_config(
                dataset_id, new_id, short_config, dry_run=dry_run)
            self.rename_wdae_dataset_and_groups(
                dataset_id, new_id, dry_run=dry_run)
