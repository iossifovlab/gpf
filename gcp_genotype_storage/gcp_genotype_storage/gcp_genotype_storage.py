import logging
from typing import Dict, Any, cast, Optional
from dataclasses import dataclass

import pyarrow.parquet as pq
from cerberus import Validator

import gcsfs
from google.cloud import bigquery

from dae.utils import fs_utils
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.parquet.partition_descriptor import PartitionDescriptor

from gcp_genotype_storage.bigquery_variants import BigQueryVariants


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
        "bigquery": {
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
        return self.storage_config["bigquery"]["db"]

    @staticmethod
    def _study_tables(study_config) -> GcpStudyLayout:
        study_id = study_config["id"]
        storage_config = study_config.get("genotype_storage")
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
            pedigree_table, summary_table, family_table, meta_table)

    def build_backend(self, study_config, genome, gene_models):
        assert study_config is not None
        tables_layout = self._study_tables(study_config)
        project_id = self.storage_config["project_id"]
        db = self.storage_config["bigquery"]["db"]
        backend = BigQueryVariants(
            project_id, db,
            tables_layout.summary_variants,
            tables_layout.family_variants,
            tables_layout.pedigree,
            tables_layout.meta,
            gene_models=gene_models)
        return backend

    def _load_partition_description(
            self, metadata_path) -> PartitionDescriptor:
        df = pq.read_table(metadata_path).to_pandas()
        for record in df.to_dict(orient="records"):
            if record["key"] == "partition_description":
                return PartitionDescriptor.parse_string(record["value"])
        return PartitionDescriptor()

    def _upload_dataset_into_import_bucket(
            self, study_id: str,
            study_dataset: GcpStudyLayout) -> GcpStudyLayout:
        """Upload a study dataset into import bucket."""
        assert self.fs is not None
        upload_path = fs_utils.join(
            self.storage_config["import_bucket"],
            self.storage_config["id"],
            self.storage_config["bigquery"]["db"],
            study_id)

        bucket_layout = GcpStudyLayout(
            fs_utils.join(upload_path, "pedigree.parquet"),
            fs_utils.join(upload_path, "summary_variants"),
            fs_utils.join(upload_path, "family_variants"),
            fs_utils.join(upload_path, "meta.parquet"))

        if self.fs.exists(upload_path):
            self.fs.rm(upload_path, recursive=True)
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

    def _load_dataset_into_bigquery(
            self, study_id: str,
            bucket_layout: GcpStudyLayout,
            partition_descriptor: PartitionDescriptor) -> GcpStudyLayout:
        client = bigquery.Client()
        dbname = self.storage_config["bigquery"]["db"]
        dataset = client.create_dataset(dbname, exists_ok=True)
        tables_layout = self._study_tables({"id": study_id})
        for table_name in [
                tables_layout.pedigree, tables_layout.meta,
                tables_layout.summary_variants,
                tables_layout.family_variants]:
            sql = f"DROP TABLE IF EXISTS {dbname}.{table_name}"
            client.query(sql).result()

        pedigree_table = dataset.table(tables_layout.pedigree)
        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.PARQUET
        job_config.autodetect = True
        pedigree_job = client.load_table_from_uri(
            bucket_layout.pedigree, pedigree_table, job_config=job_config)
        if not pedigree_job.result().done():
            logger.error("pedigree not loaded into BigQuery")
            raise ValueError("pedigree not loaded into BigQuery")

        meta_table = dataset.table(tables_layout.meta)
        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.PARQUET
        job_config.autodetect = True
        meta_job = client.load_table_from_uri(
            bucket_layout.meta, meta_table, job_config=job_config)
        if not meta_job.result().done():
            logger.error("metadata not loaded into BigQuery")
            raise ValueError("metadata not loaded into BigQuery")

        if tables_layout.summary_variants is None:
            assert tables_layout.family_variants is None
            return tables_layout

        assert tables_layout.summary_variants is not None
        assert tables_layout.family_variants is not None

        type_convertions = {
            "string": "STRING",
            "int8": "INTEGER",
        }
        summary_table = dataset.table(tables_layout.summary_variants)
        job_config = bigquery.LoadJobConfig()
        job_config.autodetect = True

        job_config.source_format = bigquery.SourceFormat.PARQUET

        parquet_options = \
            bigquery.format_options.ParquetOptions()
        parquet_options.enable_list_inference = True
        job_config.parquet_options = parquet_options

        if partition_descriptor.has_summary_partitions():
            hive_partitioning = \
                bigquery.external_config.HivePartitioningOptions()
            hive_partitioning.mode = "CUSTOM"
            summary_partition = "/".join([
                f"{{{bname}:{type_convertions[btype]}}}"
                for (bname, btype) in
                partition_descriptor.dataset_summary_partition()
            ])
            hive_partitioning.source_uri_prefix = \
                f"{bucket_layout.summary_variants}/{summary_partition}"
            job_config.hive_partitioning = hive_partitioning

        summary_job = client.load_table_from_uri(
            f"{bucket_layout.summary_variants}/*.parquet", summary_table,
            job_config=job_config)
        if not summary_job.result().done():
            logger.error("summary variants not loaded into BigQuery")
            raise ValueError("summary variants not loaded into BigQuery")

        family_table = dataset.table(tables_layout.family_variants)
        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.PARQUET
        job_config.autodetect = True
        parquet_options = \
            bigquery.format_options.ParquetOptions()
        parquet_options.enable_list_inference = True
        job_config.parquet_options = parquet_options

        if partition_descriptor.has_family_partitions():
            hive_partitioning = \
                bigquery.external_config.HivePartitioningOptions()
            hive_partitioning.mode = "CUSTOM"
            family_partition = "/".join([
                f"{{{bname}:{type_convertions[btype]}}}"
                for (bname, btype) in
                partition_descriptor.dataset_family_partition()
            ])
            hive_partitioning.source_uri_prefix = \
                f"{bucket_layout.family_variants}/{family_partition}"
            job_config.hive_partitioning = hive_partitioning

        family_job = client.load_table_from_uri(
            f"{bucket_layout.family_variants}/*.parquet", family_table,
            job_config=job_config)
        if not family_job.result().done():
            logger.error("family variants not loaded into BigQuery")
            raise ValueError("family variants not loaded into BigQuery")

        return tables_layout

    def gcp_import_dataset(
            self, study_id: str,
            study_layout: GcpStudyLayout):
        """Create pedigree and variant tables for a study."""
        partition_description = self._load_partition_description(
            study_layout.meta)
        bucket_layout = self._upload_dataset_into_import_bucket(
            study_id, study_layout)
        return self._load_dataset_into_bigquery(
            study_id, bucket_layout, partition_description)