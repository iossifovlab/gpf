import logging
import os
import time
from typing import Any, ClassVar, cast

from box import Box
from cerberus import Validator

from dae.configuration.utils import validate_path
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.inmemory_storage.annotation_serialization import (
    build_annotation_filename,
    variants_loader_load_annotation,
)
from dae.inmemory_storage.raw_variants import RawMemoryVariants
from dae.pedigrees.loader import FamiliesLoader
from dae.variants_loaders.cnv.loader import CNVLoader
from dae.variants_loaders.dae.loader import DaeTransmittedLoader, DenovoLoader
from dae.variants_loaders.raw.loader import (
    VariantsLoader,
)
from dae.variants_loaders.vcf.loader import VcfLoader

logger = logging.getLogger(__name__)


class InmemoryGenotypeStorage(GenotypeStorage):
    """A storage that uses the in-memory as its backend."""

    VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "storage_type": {"type": "string", "allowed": ["inmemory"]},
        "id": {
            "type": "string",
        },
        "read_only": {
            "type": "boolean",
            "default": False,
        },
        "dir": {
            "type": "string",
            "check_with": validate_path,
            "required": True,
        },
    }

    def __init__(self, storage_config: dict[str, Any]):
        super().__init__(storage_config)
        self.data_dir = self.storage_config["dir"]

    @classmethod
    def get_storage_types(cls) -> set[str]:
        return {"inmemory"}

    @classmethod
    def validate_and_normalize_config(cls, config: dict) -> dict:
        config = super().validate_and_normalize_config(config)
        validator = Validator(cls.VALIDATION_SCHEMA)  # pyright: ignore
        if not validator.validate(config):  # pyright: ignore
            logger.error(
                "wrong config format for inmemory genotype storage: %s",
                validator.errors)  # pyright: ignore
            raise ValueError(
                f"wrong config format for inmemory storage: "
                f"{validator.errors}")  # pyright: ignore
        return cast(dict, validator.document)  # pyright: ignore

    def start(self) -> GenotypeStorage:
        return self

    def shutdown(self) -> GenotypeStorage:
        """No resources to close."""
        return self

    def get_data_dir(self, *path: str) -> str:
        return os.path.join(self.data_dir, *path)

    def build_backend(
        self, study_config: dict[str, Any],
        genome: ReferenceGenome,
        gene_models: GeneModels | None,  # noqa: ARG002
    ) -> Any:
        start = time.time()
        config = Box(study_config)
        ped_params = \
            config.genotype_storage.files.pedigree.params.to_dict()
        ped_filename = config.genotype_storage.files.pedigree.path
        logger.debug("pedigree params: %s; %s", ped_filename, ped_params)

        families_loader = FamiliesLoader(ped_filename, **ped_params)
        families = families_loader.load()
        elapsed = time.time() - start
        logger.info("families loaded in in %.2f sec", elapsed)

        result = []
        for file_conf in config.genotype_storage.files.variants:
            start = time.time()
            variants_filename = file_conf.path
            variants_params = file_conf.params.to_dict()
            logger.debug(
                "variant params: %s; %s", variants_filename, variants_params)
            variants_loader: VariantsLoader | None = None
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
                variants_filenames = [
                    fn.strip() for fn in variants_filename.split(" ")
                ]
                variants_loader = CNVLoader(
                    families,
                    variants_filenames,
                    genome,
                    params=variants_params,
                )
            if variants_loader is None:
                raise ValueError(
                    f"unknown variant file format: {file_conf.format}")

            full_variants = variants_loader_load_annotation(
                variants_loader,
                build_annotation_filename(annotation_filename))
            result.extend(full_variants)

        return RawMemoryVariants(result, families)
