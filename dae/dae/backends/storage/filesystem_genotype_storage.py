import os
import copy
import shutil
import time

from dae.pedigrees.loader import FamiliesLoader

from dae.backends.storage.genotype_storage import GenotypeStorage

from dae.backends.raw.loader import StoredAnnotationDecorator, \
    AnnotationPipelineDecorator
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.backends.vcf.loader import VcfLoader
from dae.backends.dae.loader import DenovoLoader


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
                families, [vcf_filename])
            variants_loader = StoredAnnotationDecorator.decorate(
                variants_loader, vcf_filename
            )
            return RawMemoryVariants([variants_loader])

        else:
            start = time.time()
            families_loader = FamiliesLoader(
                study_config.files.pedigree.path,
                params=study_config.files.pedigree.params)
            families = families_loader.load()
            elapsed = time.time() - start
            print(f"Families loaded in in {elapsed:.2f} sec")

            loaders = []
            if study_config.files.vcf:
                start = time.time()
                variants_filename = study_config.files.vcf[0].path
                variants_loader = VcfLoader(
                    families, [variants_filename],
                    params=study_config.files.vcf[0].params)
                variants_loader = StoredAnnotationDecorator.decorate(
                    variants_loader, variants_filename
                )
                loaders.append(variants_loader)
            if study_config.files.denovo:

                variants_filename = study_config.files.denovo[0].path
                variants_loader = DenovoLoader(
                    families, variants_filename,
                    genomes_db.get_genome(),
                    params=study_config.files.denovo[0].params)

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

        # assert len(variant_loaders) == 1, \
        #     'Filesystem genotype storage supports only one variant file'

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
        source_filename = families_loader.families_filename
        destination_filename = os.path.join(
            self.data_dir,
            study_id,
            'data',
            os.path.basename(source_filename)
        )

        params = copy.deepcopy(families_loader.params)
        params['file_format'] = families_loader.file_format
        config = STUDY_PEDIGREE_TEMPLATE.format(
            path=destination_filename,
            params=",\n\t".join([
                "{}:{}".format(k, str(v).replace('\t', '\\t'))
                for k, v in params.items()])
        )

        os.makedirs(
            os.path.dirname(destination_filename),
            exist_ok=True)
        shutil.copyfile(source_filename, destination_filename)
        return config

    def _import_variants_files(self, study_id, loaders):
        result_config = []
        for index, variants_loader in enumerate(loaders):
            assert isinstance(variants_loader, AnnotationPipelineDecorator)

            source_filename = variants_loader.filename
            destination_filename = os.path.join(
                self.data_dir,
                study_id,
                'data',
                os.path.basename(source_filename)
            )
            params = ",\n\t".join([
                "{}:{}".format(k, v)
                for k, v in variants_loader.params.items() if v is not None])
            config = STUDY_VARIANTS_TEMPLATE.format(
                index=index,
                path=destination_filename,
                params=params,
                source_type=variants_loader.source_type
            )
            result_config.append(config)

            os.makedirs(
                os.path.dirname(destination_filename),
                exist_ok=True)
            annotation_filename = "{}-eff.txt".format(
                os.path.splitext(destination_filename)[0])
            variants_loader.save_annotation_file(annotation_filename)

            shutil.copyfile(source_filename, destination_filename)

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
