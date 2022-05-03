import logging
import os
from dae.backends.impala.parquet_io import ParquetManager
from dae.import_tools.task_graph import TaskGraph
from dae.utils import fs_utils
from dae.backends.impala.import_commons import MakefilePartitionHelper
import toml


logger = logging.getLogger(__file__)


class Schema1ParquetWriter:
    @staticmethod
    def write_variant(variants_loader, bucket_id, gpf_instance, project,
                      out_dir):
        partition_description = project.get_partition_description(
            work_dir=out_dir)

        loader_args = project.import_config["input"][bucket_id.type]
        generator = MakefilePartitionHelper(
            partition_description,
            gpf_instance.reference_genome,
            add_chrom_prefix=loader_args.get("add_chrom_prefix", None),
            del_chrom_prefix=loader_args.get("del_chrom_prefix", None),
        )

        target_chromosomes = loader_args.get("target_chromosomes", None)
        if target_chromosomes is None:
            target_chromosomes = variants_loader.chromosomes

        variants_targets = generator.generate_variants_targets(
            target_chromosomes
        )

        bucket_index = project.get_default_bucket_index(bucket_id.type)
        if bucket_id.region_bin is not None and bucket_id.region_bin != "none":
            assert bucket_id.region_bin in variants_targets, (
                bucket_id.region_bin,
                list(variants_targets.keys()),
            )

            regions = variants_targets[bucket_id.region_bin]
            bucket_index = (
                project.get_default_bucket_index(bucket_id.type)
                + generator.bucket_index(bucket_id.region_bin)
            )
            logger.info(
                f"resetting regions (rb: {bucket_id.region_bin}): {regions}")
            variants_loader.reset_regions(regions)

        variants_loader = project.build_variants_loader_pipeline(
            variants_loader, gpf_instance
        )

        rows = 20_000  # TODO get this from the config?
        logger.debug(f"argv.rows: {rows}")

        ParquetManager.variants_to_parquet(
            variants_loader,
            partition_description,
            bucket_index=bucket_index,
            rows=rows,
        )

    @staticmethod
    def write_pedigree(families, out_dir, partition_description):
        if partition_description:
            if partition_description.family_bin_size > 0:
                families = partition_description \
                    .add_family_bins_to_families(families)

        output_filename = os.path.join(out_dir, "pedigree.parquet")

        ParquetManager.families_to_parquet(families, output_filename)


class ImpalaSchema1ImportStorage:
    def __init__(self, project):
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
    def _do_write_variant(cls, project, bucket_id):
        out_dir = cls._variants_dir(project)
        gpf_instance = project.get_gpf_instance()
        Schema1ParquetWriter.write_variant(
            project.get_variant_loader(bucket_id.type,
                                       gpf_instance.reference_genome),
            bucket_id,
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

    def generate_import_task_graph(self, project) -> TaskGraph:
        graph = TaskGraph()
        pedigree_task = graph.create_task("ped task", self._do_write_pedigree,
                                          [project], [])

        bucket_tasks = []
        for b in project.get_import_variants_bucket_ids():
            task = graph.create_task(f"Task {b}", self._do_write_variant,
                                     [project, b], [])
            bucket_tasks.append(task)

        if project.has_destination():
            hdfs_task = graph.create_task(
                "hdfs copy", self._do_load_in_hdfs,
                [project], [pedigree_task] + bucket_tasks)

            graph.create_task("impala import", self._do_load_in_impala,
                              [project], [hdfs_task])

        return graph
