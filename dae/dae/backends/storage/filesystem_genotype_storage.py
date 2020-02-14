import os
import shutil
import time
import glob

from dae.pedigrees.loader import FamiliesLoader

from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.raw.loader import StoredAnnotationDecorator
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.backends.vcf.loader import VcfLoader
from dae.backends.dae.loader import DenovoLoader, DaeTransmittedLoader


class FilesystemGenotypeStorage(GenotypeStorage):

    def __init__(self, storage_config):
        super(FilesystemGenotypeStorage, self).__init__(storage_config)
        self.data_dir = self.storage_config.dir

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
            families = families_loader.load()
            variants_loader = VcfLoader(
                families, [vcf_filename], genomes_db.get_genome())
            variants_loader = StoredAnnotationDecorator.decorate(
                variants_loader, vcf_filename
            )

            return RawMemoryVariants([variants_loader])

        else:
            start = time.time()
            ped_params = study_config.files.pedigree.params
            families_loader = FamiliesLoader(
                study_config.files.pedigree.path,
                params=ped_params)
            families = families_loader.load()
            elapsed = time.time() - start
            print(f"Families loaded in in {elapsed:.2f} sec")

            loaders = []
            if study_config.files.vcf:
                start = time.time()
                variants_filename = study_config.files.vcf[0].path
                vcf_params = study_config.files.vcf[0].params

                variants_loader = VcfLoader(
                    families, [variants_filename],
                    genomes_db.get_genome(),
                    params=vcf_params)
                variants_loader = StoredAnnotationDecorator.decorate(
                    variants_loader, variants_filename
                )
                loaders.append(variants_loader)
            if study_config.files.denovo:
                denovo_params = study_config.files.denovo[0].params
                variants_filename = study_config.files.denovo[0].path
                variants_loader = DenovoLoader(
                    families, variants_filename,
                    genomes_db.get_genome(),
                    params=denovo_params)

                variants_loader = StoredAnnotationDecorator.decorate(
                    variants_loader, variants_filename
                )
                loaders.append(variants_loader)

            if study_config.files.dae:
                dae_params = study_config.files.dae[0].params
                variants_filename = study_config.files.dae[0].path
                variants_loader = DaeTransmittedLoader(
                    families, variants_filename,
                    genomes_db.get_genome(),
                    params=dae_params)

                variants_loader = StoredAnnotationDecorator.decorate(
                    variants_loader, variants_filename
                )
                loaders.append(variants_loader)

            assert len(loaders) > 0
            return RawMemoryVariants(loaders)

    def simple_study_import(
            self, study_id,
            families_loader=None,
            variant_loaders=None,
            **kwargs):

        families_config = self._import_families_file(
            study_id, families_loader)
        variants_config = self._import_variants_files(
            study_id, variant_loaders)

        return STUDY_CONFIG_TEMPLATE.format(
            study_id=study_id,
            genotype_storage=self.id,
            files="\n\n".join([families_config, variants_config])
        )

    def _import_families_file(self, study_id, families_loader):
        source_filename = families_loader.filename
        destination_filename = os.path.join(
            self.data_dir,
            study_id,
            'data',
            os.path.basename(source_filename)
        )

        params = families_loader.build_cli_params(families_loader.params)
        params = ",\n\t".join([
                f"{key}:{value}"
                for key, value in params.items() if value is not None])
        config = STUDY_PEDIGREE_TEMPLATE.format(
            path=destination_filename,
            params=params
        )

        os.makedirs(
            os.path.dirname(destination_filename),
            exist_ok=True)
        shutil.copyfile(source_filename, destination_filename)
        return config

    def _import_variants_files(self, study_id, loaders):
        result_config = []
        for index, variants_loader in enumerate(loaders):
            assert variants_loader.get_attribute("annotation_schema") \
                is not None

            destination_dirname = os.path.join(
                    self.data_dir,
                    study_id,
                    'data')

            def construct_destination_filename(fn):
                return os.path.join(
                    destination_dirname,
                    os.path.basename(fn)
                )

            source_filenames = variants_loader.variants_filenames
            destination_filenames = list(
                map(construct_destination_filename, source_filenames))
            params = variants_loader.build_cli_params(variants_loader.params)

            params = ",\n\t".join([
                f"{key}:{value}"
                for key, value in params.items() if value is not None])
            source_type = variants_loader.get_attribute('source_type')

            config = STUDY_VARIANTS_TEMPLATE.format(
                index=index,
                path=' '.join(destination_filenames),
                params=params,
                source_type=source_type
            )
            print(config)
            result_config.append(config)

            os.makedirs(destination_dirname, exist_ok=True)
            annotation_filename = StoredAnnotationDecorator\
                .build_annotation_filename(destination_filenames[0])
            StoredAnnotationDecorator.save_annotation_file(
                variants_loader, annotation_filename)

            for filename in variants_loader.filenames:
                source_filenames = glob.glob(f'{filename}*')
                print("source filenames:", source_filenames)
                for fn in source_filenames:
                    print("copying:", fn, construct_destination_filename(fn))
                    shutil.copyfile(fn, construct_destination_filename(fn))

        return "\n\n".join(result_config)


STUDY_PEDIGREE_TEMPLATE = '''

family.path = {path}
family.format = pedigree
family.params = {params}
'''

STUDY_VARIANTS_TEMPLATE = '''
{index}.path = {path}
{index}.format = {source_type}
{index}.params = {params}
'''

STUDY_CONFIG_TEMPLATE = '''
[genotypeDataStudy]
id = {study_id}
genotype_storage = {genotype_storage}


[files]
{files}
'''
