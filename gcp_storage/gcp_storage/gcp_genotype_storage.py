import logging
from typing import Any, ClassVar, Optional, cast

import gcsfs
import pyarrow.parquet as pq
from cerberus import Validator
from google.cloud import bigquery

from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.schema2_storage.schema2_import_storage import Schema2DatasetLayout
from dae.utils import fs_utils
from gcp_storage.bigquery_variants import BigQueryVariants

logger = logging.getLogger(__name__)


class GcpGenotypeStorage(GenotypeStorage):
    """Defines Google Cloud Platform (GCP) genotype storage."""

    VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "storage_type": {"type": "string", "allowed": ["gcp"]},
        "id": {
            "type": "string", "required": True,
        },
        "project_id": {
            "type": "string", "required": True,
        },
        "import_bucket": {
            "type": "string", "required": True,
        },
        "bigquery": {
            "type": "dict",
            "schema": {
                "db": {
                    "type": "string", "required": True,
                },
                "pool_size": {
                    "type": "integer", "default": 1,
                },
            },
            "required": True,
        },
    }

    def __init__(self, storage_config: dict[str, Any]) -> None:
        super().__init__(storage_config)
        self.fs: Optional[gcsfs.GCSFileSystem] = None

    @classmethod
    def validate_and_normalize_config(cls, config: dict) -> dict:
        config = super().validate_and_normalize_config(config)
        validator = Validator(cls.VALIDATION_SCHEMA)
        if not validator.validate(config):
            logger.error(
                "wrong config format for impala genotype storage: %s",
                validator.errors)
            raise ValueError(
                f"wrong config format for impala storage: "
                f"{validator.errors}")
        return cast(dict, validator.document)

    @classmethod
    def get_storage_types(cls) -> set[str]:
        return {"gcp"}

    def start(self) -> "GcpGenotypeStorage":
        project_id = self.storage_config["project_id"]
        self.fs = gcsfs.GCSFileSystem(project=project_id)
        return self

    def shutdown(self) -> GenotypeStorage:
        self.fs = None
        return self

    def get_db(self) -> str:
        return cast(str, self.storage_config["bigquery"]["db"])

    @staticmethod
    def study_tables(
        study_config: dict[str, Any],
    ) -> Schema2DatasetLayout:
        """Construct a Schema2 study layout from a study config."""
        study_id = study_config["id"]
        storage_config = study_config.get("genotype_storage")
        has_tables = storage_config and storage_config.get("tables")
        tables = None
        family_table = f"{study_id}_family_alleles"
        summary_table = f"{study_id}_summary_alleles"
        pedigree_table = f"{study_id}_pedigree"
        meta_table = f"{study_id}_meta"

        if has_tables:
            assert storage_config is not None
            tables = storage_config["tables"]

            if tables.get("family"):
                family_table = tables["family"]

            if tables.get("summary"):
                summary_table = tables["summary"]

            if tables.pedigree:
                pedigree_table = tables.pedigree

            if tables.get("meta"):
                meta_table = tables["meta"]

        return Schema2DatasetLayout(
            study_id, pedigree_table, summary_table, family_table, meta_table)

    def build_backend(
        self, study_config: dict[str, Any],
        genome: ReferenceGenome,  # noqa: ARG002
        gene_models: GeneModels,
    ) -> BigQueryVariants:
        assert study_config is not None
        tables_layout = self.study_tables(study_config)
        project_id = self.storage_config["project_id"]
        db = self.storage_config["bigquery"]["db"]
        return BigQueryVariants(
            project_id, db,
            tables_layout.summary,
            tables_layout.family,
            tables_layout.pedigree,
            tables_layout.meta,
            gene_models=gene_models)

    def _load_partition_description(
            self, metadata_path: str) -> PartitionDescriptor:
        df = pq.read_table(metadata_path).to_pandas()
        for record in df.to_dict(orient="records"):
            if record["key"] == "partition_description":
                return PartitionDescriptor.parse_string(record["value"])
        return PartitionDescriptor()

    def _upload_dataset_into_import_bucket(
            self, study_id: str,
            study_dataset: Schema2DatasetLayout) -> Schema2DatasetLayout:
        """Upload a study dataset into import bucket."""
        assert self.fs is not None
        upload_path = fs_utils.join(
            self.storage_config["import_bucket"],
            self.storage_config["id"],
            self.storage_config["bigquery"]["db"],
            study_id)

        bucket_layout = Schema2DatasetLayout(
            study_id,
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
            study_dataset.summary,
            bucket_layout.summary,
            recursive=True)
        self.fs.put(
            study_dataset.family,
            bucket_layout.family,
            recursive=True)
        return bucket_layout

    def _load_dataset_into_bigquery(
            self, study_id: str,
            bucket_layout: Schema2DatasetLayout,
            partition_descriptor: PartitionDescriptor) -> Schema2DatasetLayout:
        # pylint: disable=too-many-locals,too-many-statements
        client = bigquery.Client()
        dbname = self.storage_config["bigquery"]["db"]
        dataset = client.create_dataset(dbname, exists_ok=True)
        tables_layout = self.study_tables({"id": study_id})
        for table_name in [
                tables_layout.pedigree, tables_layout.meta,
                tables_layout.summary,
                tables_layout.family]:
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

        assert tables_layout.meta is not None
        meta_table = dataset.table(tables_layout.meta)
        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.PARQUET
        job_config.autodetect = True
        assert bucket_layout.meta is not None
        meta_job = client.load_table_from_uri(
            bucket_layout.meta, meta_table, job_config=job_config)
        if not meta_job.result().done():
            logger.error("metadata not loaded into BigQuery")
            raise ValueError("metadata not loaded into BigQuery")

        if tables_layout.summary is None:
            assert tables_layout.family is None
            return tables_layout

        assert tables_layout.summary is not None
        assert tables_layout.family is not None

        type_convertions = {
            "string": "STRING",
            "int8": "INTEGER",
        }
        summary_table = dataset.table(tables_layout.summary)
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
                f"{bucket_layout.summary}/{summary_partition}"
            job_config.hive_partitioning = hive_partitioning

        summary_job = client.load_table_from_uri(
            f"{bucket_layout.summary}/*.parquet", summary_table,
            job_config=job_config)
        if not summary_job.result().done():
            logger.error("summary variants not loaded into BigQuery")
            raise ValueError("summary variants not loaded into BigQuery")

        family_table = dataset.table(tables_layout.family)
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
                f"{bucket_layout.family}/{family_partition}"
            job_config.hive_partitioning = hive_partitioning

        family_job = client.load_table_from_uri(
            f"{bucket_layout.family}/*.parquet", family_table,
            job_config=job_config)
        if not family_job.result().done():
            logger.error("family variants not loaded into BigQuery")
            raise ValueError("family variants not loaded into BigQuery")

        return tables_layout

    def gcp_import_dataset(
            self, study_id: str,
            study_layout: Schema2DatasetLayout) -> Schema2DatasetLayout:
        """Create pedigree and variant tables for a study."""
        partition_description = self._load_partition_description(
            study_layout.meta)
        bucket_layout = self._upload_dataset_into_import_bucket(
            study_id, study_layout)
        return self._load_dataset_into_bigquery(
            study_id, bucket_layout, partition_description)
