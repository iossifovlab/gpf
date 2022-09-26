import os
import shutil
import time
import glob
import logging
from typing import Dict, Any, cast

from cerberus import Validator

from dae.configuration.utils import validate_path
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.pedigrees.loader import FamiliesLoader

from dae.genotype_storage.genotype_storage import GenotypeStorage

from dae.backends.raw.loader import StoredAnnotationDecorator
from dae.backends.raw.raw_variants import RawMemoryVariants

from dae.backends.vcf.loader import VcfLoader
from dae.backends.dae.loader import DenovoLoader, DaeTransmittedLoader
from dae.backends.cnv.loader import CNVLoader

from dae.utils.dict_utils import recursive_dict_update

logger = logging.getLogger(__name__)


class FilesystemGenotypeStorage(GenotypeStorage):
    """A storage that uses the filesystem as its backend."""

    VALIDATION_SCHEMA = {
        "storage_type": {"type": "string", "allowed": ["filesystem"]},
        "id": {
            "type": "string",
        },
        "dir": {
            "type": "string",
            "check_with": validate_path,
            "required": True,
        },
    }

    def __init__(self, storage_config: Dict[str, Any]):
        super().__init__(storage_config)
        self.data_dir = self.storage_config["dir"]

    @classmethod
    def validate_config(cls, config: Dict) -> Dict:
        config = super().validate_config(config)
        validator = Validator(cls.VALIDATION_SCHEMA)
        if not validator.validate(config):
            logger.error(
                "wrong config format for fileystem genotype storage: %s",
                validator.errors)
            raise ValueError(
                f"wrong config format for filesytem storage: "
                f"{validator.errors}")
        return cast(Dict, validator.document)

    def start(self):
        return self

    def shutdown(self):
        """No resources to close."""

    def get_data_dir(self, *path):
        return os.path.join(self.data_dir, *path)

    def build_backend(self, study_config, genome, gene_models):
        start = time.time()
        ped_params = \
            study_config.genotype_storage.files.pedigree.params.to_dict()
        ped_filename = study_config.genotype_storage.files.pedigree.path
        logger.debug("pedigree params: %s; %s", ped_filename, ped_params)

        families_loader = FamiliesLoader(ped_filename, **ped_params)
        families = families_loader.load()
        elapsed = time.time() - start
        logger.info("families loaded in in %.2f sec", elapsed)

        loaders = []
        for file_conf in study_config.genotype_storage.files.variants:
            start = time.time()
            variants_filename = file_conf.path
            variants_params = file_conf.params.to_dict()
            logger.debug(
                "variant params: %s; %s", variants_filename, variants_params)

            annotation_filename = variants_filename
            if file_conf.format == "vcf":
                variants_filenames = [
                    fn.strip() for fn in variants_filename.split(" ")
                ]
                variants_loader = VcfLoader(
                    families,
                    variants_filenames,
                    genome,
                    params=variants_params,
                )
                annotation_filename = variants_filenames[0]
            if file_conf.format == "denovo":
                variants_loader = DenovoLoader(
                    families,
                    variants_filename,
                    genome,
                    params=variants_params,
                )
            if file_conf.format == "dae":
                variants_loader = DaeTransmittedLoader(
                    families,
                    variants_filename,
                    genome,
                    params=variants_params,
                )
            if file_conf.format == "cnv":
                variants_loader = CNVLoader(
                    families,
                    variants_filename,
                    genome,
                    params=variants_params,
                )

            variants_loader = StoredAnnotationDecorator.decorate(
                variants_loader, annotation_filename
            )
            loaders.append(variants_loader)

        return RawMemoryVariants(loaders, families)

    def simple_study_import(
        self,
        study_id,
        families_loader=None,
        variant_loaders=None,
        study_config=None,
        **kwargs,
    ):

        families_config = self._import_families_file(study_id, families_loader)
        variants_config = self._import_variants_files(
            study_id, variant_loaders
        )

        config_dict = {
            "id": study_id,
            "conf_dir": ".",
            "has_denovo": False,
            "has_cnv": False,
            "genotype_storage": {
                "id": self.storage_id,
                "files": {
                    "variants": variants_config,
                    "pedigree": families_config,
                },
            },
            "genotype_browser": {"enabled": True},
        }
        if not variant_loaders:
            config_dict["genotype_browser"]["enabled"] = False
        else:
            variant_loaders[0].get_attribute("source_type")
            if any(
                    loader.get_attribute("source_type") == "denovo"
                    for loader in variant_loaders):
                config_dict["has_denovo"] = True
            if any(
                    loader.get_attribute("source_type") == "cnv"
                    for loader in variant_loaders):
                config_dict["has_denovo"] = True  # FIXME
                config_dict["has_cnv"] = True

        if study_config is not None:
            study_config_dict = GPFConfigParser.load_config_raw(study_config)
            config_dict = recursive_dict_update(config_dict, study_config_dict)

        config_builder = StudyConfigBuilder(config_dict)
        return config_builder.build_config()

    def _import_families_file(self, study_id, families_loader):
        source_filename = families_loader.filename
        destination_filename = os.path.join(
            self.data_dir, study_id, "data", os.path.basename(source_filename)
        )

        params = families_loader.build_arguments_dict()
        for key, value in params.items():
            if isinstance(value, bool):
                params[key] = "true" if value else "false"
            if isinstance(value, str) and "\t" in value:
                value = value.replace("\t", "\\t")
                params[key] = value

        config = {"path": destination_filename, "params": params}

        os.makedirs(os.path.dirname(destination_filename), exist_ok=True)
        shutil.copyfile(source_filename, destination_filename)
        return config

    def _import_variants_files(self, study_id, loaders):
        result_config = []
        destination_dirname = os.path.join(self.data_dir, study_id, "data")
        for variants_loader in loaders:

            def construct_destination_filename(fname):
                return os.path.join(
                    destination_dirname, os.path.basename(fname))

            source_filenames = variants_loader.variants_filenames
            destination_filenames = list(
                map(construct_destination_filename, source_filenames)
            )
            params = variants_loader.build_arguments_dict()
            source_type = variants_loader.get_attribute("source_type")
            for key, value in params.items():
                if isinstance(value, bool):
                    params[key] = "true" if value else "false"
                if isinstance(value, str) and "\t" in value:
                    value = value.replace("\t", "\\t")
                    params[key] = value
            config = {
                "path": " ".join(destination_filenames),
                "params": params,
                "format": source_type,
            }
            logger.debug("config prepared: %s", config)
            result_config.append(config)

            os.makedirs(destination_dirname, exist_ok=True)
            annotation_filename = \
                StoredAnnotationDecorator.build_annotation_filename(
                    destination_filenames[0]
                )
            StoredAnnotationDecorator.save_annotation_file(
                variants_loader, annotation_filename
            )

            for filename in variants_loader.filenames:
                source_filenames = glob.glob(f"{filename}*")
                logger.debug("source filenames: %s", source_filenames)
                for fname in source_filenames:
                    logger.debug(
                        "copying: %s -> %s",
                        fname, construct_destination_filename(fname))
                    shutil.copyfile(
                        fname, construct_destination_filename(fname))

        return result_config
