import os
import time
import logging
from typing import Dict, Any, cast

from cerberus import Validator

from dae.configuration.utils import validate_path
from dae.pedigrees.loader import FamiliesLoader

from dae.genotype_storage.genotype_storage import GenotypeStorage

from dae.variants_loaders.raw.loader import StoredAnnotationDecorator
from dae.filesystem_storage.in_memory.raw_variants import RawMemoryVariants

from dae.variants_loaders.vcf.loader import VcfLoader
from dae.variants_loaders.dae.loader import DenovoLoader, DaeTransmittedLoader
from dae.variants_loaders.cnv.loader import CNVLoader

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
    def get_storage_type(cls) -> str:
        return "filesystem"

    @classmethod
    def validate_and_normalize_config(cls, config: Dict) -> Dict:
        config = super().validate_and_normalize_config(config)
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
                variants_filenames = [
                    fn.strip() for fn in variants_filename.split(" ")
                ]
                variants_loader = DaeTransmittedLoader(
                    families,
                    variants_filenames[0],
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
