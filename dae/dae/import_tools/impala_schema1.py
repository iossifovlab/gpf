import logging
import os
from dae.backends.impala.parquet_io import ParquetManager, \
    ParquetPartitionDescriptor, PartitionDescriptor
from dae.import_tools.import_tools import AbstractImportStorage
from dae.import_tools.task_graph import TaskGraph
from dae.pedigrees.family import FamiliesData
from dae.utils import fs_utils
import toml


logger = logging.getLogger(__file__)


class Schema1ParquetWriter:
    @staticmethod
    def write_variant(variants_loader, bucket, gpf_instance, project,
                      out_dir):
        partition_description = project.get_partition_description(
            work_dir=out_dir)

        if bucket.region_bin is not None and bucket.region_bin != "none":
            logger.info(
                f"resetting regions (rb: {bucket.region_bin}): "
                f"{bucket.regions}")
            variants_loader.reset_regions(bucket.regions)

        variants_loader = project.build_variants_loader_pipeline(
            variants_loader, gpf_instance
        )

        rows = project.get_row_group_size(bucket)
        logger.debug(f"argv.rows: {rows}")

        ParquetManager.variants_to_parquet(
            variants_loader,
            partition_description,
            bucket_index=bucket.index,
            rows=rows,
        )

    @staticmethod
    def write_pedigree(families: FamiliesData, out_dir: str,
                       partition_description: PartitionDescriptor):
        if isinstance(partition_description, ParquetPartitionDescriptor):
            if partition_description.family_bin_size > 0:
                families = partition_description \
                    .add_family_bins_to_families(families)

        output_filename = os.path.join(out_dir, "pedigree.parquet")

        ParquetManager.families_to_parquet(families, output_filename)


class ImpalaSchema1ImportStorage(AbstractImportStorage):
    """This class encodes the logic for import data in the
    Impala Schema 1 format"""
    def __init__(self, project):
        super().__init__(project)
        self.project = project

    @staticmethod
    def _pedigree_dir(project):
        return fs_utils.join(project.work_dir, f"{project.study_id}_pedigree")

    @staticmethod
    def _variants_dir(project):
        return fs_utils.join(project.work_dir, f"{project.study_id}_variants")

    @classmethod
    def _do_write_pedigree(cls, project):
        out_dir = cls._pedigree_dir(project)
        Schema1ParquetWriter.write_pedigree(
            project.get_pedigree(), out_dir,
            project.get_partition_description()
        )

    @classmethod
    def _do_write_variant(cls, project, bucket):
        out_dir = cls._variants_dir(project)
        gpf_instance = project.get_gpf_instance()
        Schema1ParquetWriter.write_variant(
            project.get_variant_loader(bucket,
                                       gpf_instance.reference_genome),
            bucket,
            gpf_instance,
            project, out_dir)

    @classmethod
    def _do_load_in_hdfs(cls, project):
        gpf_instance = project.get_gpf_instance()
        genotype_storage_db = gpf_instance.genotype_storage_db
        genotype_storage = genotype_storage_db.get_genotype_storage(
            project.genotype_storage_id
        )
        if genotype_storage is None or not genotype_storage.is_impala():
            logger.error("missing or non-impala genotype storage")
            return

        partition_description = project.get_partition_description()

        pedigree_file = fs_utils.join(cls._pedigree_dir(project),
                                      "pedigree.parquet")
        genotype_storage.hdfs_upload_dataset(
            project.study_id,
            cls._variants_dir(project),
            pedigree_file,
            partition_description)

    @classmethod
    def _do_load_in_impala(cls, project):
        gpf_instance = project.get_gpf_instance()
        genotype_storage_db = gpf_instance.genotype_storage_db
        genotype_storage = genotype_storage_db.get_genotype_storage(
            project.genotype_storage_id)

        if genotype_storage is None or not genotype_storage.is_impala():
            logger.error("missing or non-impala genotype storage")
            return

        study_id = project.study_id

        hdfs_variants_dir = \
            genotype_storage.default_variants_hdfs_dirname(study_id)

        hdfs_pedigree_file = \
            genotype_storage.default_pedigree_hdfs_filename(project.study_id)

        logger.info(f"HDFS variants dir: {hdfs_variants_dir}")
        logger.info(f"HDFS pedigree file: {hdfs_pedigree_file}")

        partition_description = project.get_partition_description()

        variants_schema_fn = fs_utils.join(
            cls._variants_dir(project), "_VARIANTS_SCHEMA")
        with open(variants_schema_fn) as infile:
            content = infile.read()
            schema = toml.loads(content)
            variants_schema = schema["variants_schema"]

        genotype_storage.impala_import_dataset(
            project.study_id,
            hdfs_pedigree_file,
            hdfs_variants_dir,
            partition_description=partition_description,
            variants_schema=variants_schema)

    def generate_import_task_graph(self) -> TaskGraph:
        graph = TaskGraph()
        pedigree_task = graph.create_task("ped task", self._do_write_pedigree,
                                          [self.project], [])

        bucket_tasks = []
        for b in self.project.get_import_variants_buckets():
            task = graph.create_task(f"Task {b}", self._do_write_variant,
                                     [self.project, b], [])
            bucket_tasks.append(task)

        if self.project.has_destination():
            hdfs_task = graph.create_task(
                "hdfs copy", self._do_load_in_hdfs,
                [self.project], [pedigree_task] + bucket_tasks)

            graph.create_task("impala import", self._do_load_in_impala,
                              [self.project], [hdfs_task])

        return graph
