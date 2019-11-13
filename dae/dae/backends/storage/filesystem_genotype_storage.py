import os

from dae.pedigrees.pedigree_reader import PedigreeReader
from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.vcf.loader import RawVcfLoader
from dae.backends.dae.loader import RawDaeLoader


class FilesystemGenotypeStorage(GenotypeStorage):

    def __init__(self, storage_config):
        super(FilesystemGenotypeStorage, self).__init__(storage_config)

    def get_data_dir(self, *path):
        return os.path.abspath(
            os.path.join(self.storage_config.dir, *path)
        )

    def is_filestorage(self):
        return True

    def build_backend(self, study_config, genomes_db):
        if study_config.files is None:
            data_dir = self.get_data_dir(study_config.id, 'data')
            vcf_filename = os.path.join(
                data_dir, "{}.vcf".format(study_config.id))
            ped_filename = os.path.join(
                data_dir, "{}.ped".format(study_config.id))
            ped_df = PedigreeReader.flexible_pedigree_read(ped_filename)
            return RawVcfLoader.load_raw_vcf_variants(
                ped_df, vcf_filename
            )
        elif study_config.files.vcf is not None:

            ped_df = PedigreeReader.flexible_pedigree_read(
                study_config.files.pedigree)
            return RawVcfLoader.load_raw_vcf_variants(
                ped_df, study_config.files.vcf
            )

        else:
            assert study_config.files.denovo is not None
            ped_filename = study_config.files.pedigree
            denovo_filename = study_config.files.denovo
            annotation_filename = RawDaeLoader.annotation_filename(
                denovo_filename)
            return RawDaeLoader.load_raw_denovo_variants(
                ped_filename, denovo_filename, annotation_filename)
