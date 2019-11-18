import os
import shutil

from dae.pedigrees.family import PedigreeReader
from dae.pedigrees.family import FamiliesData

from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.raw.loader import RawVariantsLoader
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.backends.vcf.loader import VcfLoader
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

            families = FamiliesData.load_pedigree(ped_filename)
            variants_loader = VcfLoader(families, vcf_filename)
            return RawMemoryVariants(variants_loader)

        elif study_config.files.vcf is not None:
            families = FamiliesData.load_pedigree(study_config.files.pedigree)
            variants_loader = VcfLoader(study_config.files.vcf)
            return RawMemoryVariants(variants_loader)

        else:
            assert study_config.files.denovo is not None
            ped_filename = study_config.files.pedigree
            denovo_filename = study_config.files.denovo
            annotation_filename = RawDaeLoader._build_annotation_filename(
                denovo_filename)
            return RawDaeLoader.load_raw_denovo_variants(
                ped_filename, denovo_filename, annotation_filename)

    def _import_variants_common(self, study_id, fvars):
        data_dir = self.get_data_dir(study_id, 'data')
        pedigree_filename = os.path.join(data_dir, f"{study_id}.ped")
        PedigreeReader.save_pedigree(
            fvars.families.ped_df, pedigree_filename)
        annotation_filename = os.path.join(data_dir, f"{study_id}-eff.txt")
        RawVariantsLoader.save_annotation_file(
            fvars.annot_df, annotation_filename)
        return data_dir

    def simple_import_denovo_variants(self, study_id, fvars):
        data_dir = self._import_variants_common(study_id, fvars)
        denovo_filename = os.path.join(data_dir, f"{study_id}.tsv")
        RawDaeLoader.save_dae_denovo_file(fvars.denovo_df, denovo_filename)

    def simple_import_vcf_variants(self, study_id, fvars):
        self._import_variants_common(study_id, fvars)
        data_dir = self._import_variants_common(study_id, fvars)
        vcf_filename = os.path.join(data_dir, f"{study_id}.vcf")
        shutil.copyfile(fvars.source_filename, vcf_filename)
