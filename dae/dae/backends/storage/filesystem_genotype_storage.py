import os

from dae.pedigrees.family import FamiliesLoader

from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.raw.loader import StoredAnnotationDecorator
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.backends.vcf.loader import VcfLoader
from dae.backends.dae.loader import DenovoLoader


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

            families_loader = FamiliesLoader(ped_filename)
            variants_loader = VcfLoader(
                families_loader.families, vcf_filename)
            variants_loader = StoredAnnotationDecorator.decorate(
                variants_loader, vcf_filename
            )
            return RawMemoryVariants(variants_loader)

        elif study_config.files.vcf is not None:
            families_loader = FamiliesLoader(study_config.files.pedigree.path)
            vcf_filename = study_config.files.vcf[0].path
            variants_loader = VcfLoader(families_loader.families, vcf_filename)
            variants_loader = StoredAnnotationDecorator.decorate(
                variants_loader, vcf_filename
            )
            return RawMemoryVariants(variants_loader)

        else:
            assert study_config.files.denovo is not None
            families_loader = FamiliesLoader(study_config.files.pedigree.path)
            denovo_filename = study_config.files.denovo[0].path
            variants_loader = DenovoLoader(
                families_loader.familes, denovo_filename)
            variants_loader = StoredAnnotationDecorator.decorate(
                variants_loader, denovo_filename
            )
            return RawMemoryVariants(variants_loader)

    # def _import_variants_common(self, study_id, fvars):
    #     data_dir = self.get_data_dir(study_id, 'data')
    #     pedigree_filename = os.path.join(data_dir, f"{study_id}.ped")
    #     PedigreeReader.save_pedigree(
    #         fvars.families.ped_df, pedigree_filename)
    #     annotation_filename = os.path.join(data_dir, f"{study_id}-eff.txt")
    #     RawVariantsLoader.save_annotation_file(
    #         fvars.annot_df, annotation_filename)
    #     return data_dir

    # def simple_import_denovo_variants(self, study_id, fvars):
    #     data_dir = self._import_variants_common(study_id, fvars)
    #     denovo_filename = os.path.join(data_dir, f"{study_id}.tsv")
    #     RawDaeLoader.save_dae_denovo_file(fvars.denovo_df, denovo_filename)

    # def simple_import_vcf_variants(self, study_id, fvars):
    #     self._import_variants_common(study_id, fvars)
    #     data_dir = self._import_variants_common(study_id, fvars)
    #     vcf_filename = os.path.join(data_dir, f"{study_id}.vcf")
    #     shutil.copyfile(fvars.source_filename, vcf_filename)
