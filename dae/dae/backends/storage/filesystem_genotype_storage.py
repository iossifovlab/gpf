import os

from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.vcf.raw_vcf import RawFamilyVariants


class FilesystemGenotypeStorage(GenotypeStorage):

    def __init__(self, storage_config):
        super(FilesystemGenotypeStorage, self).__init__(storage_config)

    def get_backend(self, study_config, genomes_db):
        data_path = self._get_data_path(study_config.id)

        variants = RawFamilyVariants(
            prefix=os.path.join(data_path, study_config.id),
            genomes_db=genomes_db
        )

        return variants
