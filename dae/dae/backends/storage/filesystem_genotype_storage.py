import os
import shutil
import time
import glob

import toml

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.study_config_builder import StudyConfigBuilder
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
        if not study_config.genotype_storage.files:
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

            return RawMemoryVariants([variants_loader], families)

        else:
            start = time.time()
            ped_params = GPFConfigParser._namedtuple_to_dict(
                study_config.genotype_storage.files.pedigree.params
            )
            families_loader = FamiliesLoader(
                study_config.genotype_storage.files.pedigree.path,
                params=ped_params
            )
            families = families_loader.load()
            elapsed = time.time() - start
            print(f"Families loaded in in {elapsed:.2f} sec")

            loaders = []
            for file_conf in study_config.genotype_storage.files.variants:
                start = time.time()
                variants_filename = file_conf.path
                variants_params = GPFConfigParser._namedtuple_to_dict(
                    file_conf.params
                )
                annotation_filename = variants_filename
                if file_conf.format == "vcf":
                    variants_filenames = [
                        fn.strip() for fn in variants_filename.split(' ')
                    ]
                    variants_loader = VcfLoader(
                        families, variants_filenames,
                        genomes_db.get_genome(),
                        params=variants_params)
                    annotation_filename = variants_filenames[0]
                if file_conf.format == "denovo":
                    variants_loader = DenovoLoader(
                        families, variants_filename,
                        genomes_db.get_genome(),
                        params=variants_params)
                if file_conf.format == "dae":
                    variants_loader = DaeTransmittedLoader(
                        families, variants_filename,
                        genomes_db.get_genome(),
                        params=variants_params)

                variants_loader = StoredAnnotationDecorator.decorate(
                    variants_loader, annotation_filename
                )
                loaders.append(variants_loader)

            return RawMemoryVariants(loaders, families)

    def simple_study_import(
            self, study_id,
            families_loader=None,
            variant_loaders=None,
            **kwargs):

        families_config = self._import_families_file(
            study_id, families_loader)
        variants_config = self._import_variants_files(
            study_id, variant_loaders)

        study_config = {
            "id": study_id,
            "conf_dir": ".",
            "has_denovo": False,
            "genotype_storage": {
                "id": self.storage_config.section_id(),
                "files": {
                    "variants": variants_config,
                    "pedigree": families_config,
                }
            },
            "genotype_browser": {
                "enabled": True
            }
        }
        if not variant_loaders:
            study_config['genotype_browser']['enabled'] = False
        else:
            variant_loaders[0].get_attribute('source_type')
            if any([l.get_attribute('source_type') == 'denovo'
                    for l in variant_loaders]):
                study_config['has_denovo'] = True
        study_dir = os.path.join(self.data_dir, study_id)
        config_builder = StudyConfigBuilder(study_config, study_dir)
        return config_builder.build_config()

    def _import_families_file(self, study_id, families_loader):
        source_filename = families_loader.filename
        destination_filename = os.path.join(
            self.data_dir,
            study_id,
            'data',
            os.path.basename(source_filename)
        )

        params = families_loader.build_cli_params(families_loader.params)

        config = {
            "path": destination_filename,
            "params": params
        }

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
            source_type = variants_loader.get_attribute('source_type')

            config = {
                "path": ' '.join(destination_filenames),
                "params": params,
                "format": source_type
            }

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

        return result_config
