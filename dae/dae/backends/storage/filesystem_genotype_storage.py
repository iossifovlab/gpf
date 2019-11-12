import os

from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.vcf.loader import RawVcfLoader


class FilesystemGenotypeStorage(GenotypeStorage):

    def __init__(self, storage_config):
        super(FilesystemGenotypeStorage, self).__init__(storage_config)

    def get_data_dir(self, *path):
        return os.path.abspath(
            os.path.join(self.storage_config.dir, *path)
        )

    def is_filestorage(self):
        return True

    def get_backend(self, study_id, genomes_db):
        data_path = self.get_data_dir(study_id, 'data', study_id)

        variants = RawVcfLoader.load_raw_vcf_variants_from_prefix(
            prefix=data_path
        )

        return variants
