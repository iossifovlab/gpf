import logging
from typing import Dict, Any, cast, Optional
from dataclasses import dataclass

from cerberus import Validator

import gcsfs

from dae.utils import fs_utils
from dae.genotype_storage.genotype_storage import GenotypeStorage


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GcpStudyLayout:
    pedigree: str
    summary_variants: Optional[str]
    family_variants: Optional[str]
    meta: str


class GcpGenotypeStorage(GenotypeStorage):
    """Defines Google Cloud Platform (GCP) genotype storage."""

    VALIDATION_SCHEMA = {
        "storage_type": {"type": "string", "allowed": ["gcp"]},
        "id": {
            "type": "string", "required": True
        },
        "project_id": {
            "type": "string", "required": True
        },
        "import_bucket": {
            "type": "string", "required": True
        },
        "big_query": {
            "type": "dict",
            "schema": {
                "db": {
                    "type": "string", "required": True
                },
                "pool_size": {
                    "type": "integer", "default": 1
                },
            },
            "required": True,
        },
    }

    def __init__(self, storage_config: Dict[str, Any]):
        super().__init__(storage_config)
        self.fs: Optional[gcsfs.GCSFileSystem] = None

    @classmethod
    def validate_and_normalize_config(cls, config: Dict) -> Dict:
        config = super().validate_and_normalize_config(config)
        validator = Validator(cls.VALIDATION_SCHEMA)
        if not validator.validate(config):
            logger.error(
                "wrong config format for impala genotype storage: %s",
                validator.errors)
            raise ValueError(
                f"wrong config format for impala storage: "
                f"{validator.errors}")
        return cast(Dict, validator.document)

    @classmethod
    def get_storage_type(cls) -> str:
        return "gcp"

    def start(self):
        project_id = self.storage_config["project_id"]
        self.fs = gcsfs.GCSFileSystem(project=project_id)
        return self

    def shutdown(self):
        self.fs = None

    def get_db(self):
        return self.storage_config["big_query"]["db"]

    @staticmethod
    def _study_tables(study_config) -> GcpStudyLayout:
        study_id = study_config.id
        storage_config = study_config.genotype_storage
        has_tables = storage_config and storage_config.get("tables")
        tables = storage_config["tables"] if has_tables else None

        family_table = f"{study_id}_family_alleles"
        if has_tables and tables.get("family"):
            family_table = tables["family"]

        summary_table = f"{study_id}_summary_alleles"
        if has_tables and tables.get("summary"):
            summary_table = tables["summary"]

        pedigree_table = f"{study_id}_pedigree"
        if has_tables and tables.pedigree:
            pedigree_table = tables.pedigree

        meta_table = f"{study_id}_meta"
        if has_tables and tables.get("meta"):
            meta_table = tables["meta"]

        return GcpStudyLayout(
            family_table, summary_table, pedigree_table, meta_table)

    def build_backend(self, study_config, genome, gene_models):
        assert study_config is not None
        raise NotImplementedError("not implemented yet")

    def _upload_dataset_into_import_bucket(
            self, study_id: str,
            study_dataset: GcpStudyLayout) -> GcpStudyLayout:
        """Upload a study dataset into import bucket."""
        assert self.fs is not None
        upload_path = fs_utils.join(
            self.storage_config["import_bucket"],
            self.storage_config["id"],
            self.storage_config["big_query"]["db"],
            study_id)

        bucket_layout = GcpStudyLayout(
            fs_utils.join(upload_path, "pedigree.parquet"),
            fs_utils.join(upload_path, "meta.parquet"),
            fs_utils.join(upload_path, "summary_variants"),
            fs_utils.join(upload_path, "family_variants"))

        if self.fs.exists(upload_path):
            self.fs.rmdir(upload_path)
        self.fs.mkdir(upload_path, create_parents=True)
        self.fs.put(
            study_dataset.pedigree,
            bucket_layout.pedigree)
        self.fs.put(
            study_dataset.meta,
            bucket_layout.meta)
        self.fs.put(
            study_dataset.summary_variants,
            bucket_layout.summary_variants,
            recursive=True)
        self.fs.put(
            study_dataset.family_variants,
            bucket_layout.family_variants,
            recursive=True)
        return bucket_layout

    def gcp_import_dataset(
            self, study_id: str,
            study_dataset: GcpStudyLayout):
        """Create pedigree and variant tables for a study."""
        bucket_layout = self._upload_dataset_into_import_bucket(
            study_id, study_dataset)
