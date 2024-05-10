import logging
import time
from collections.abc import Iterator
from typing import List, Optional, Tuple, cast

import toml

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.import_tools.import_tools import (
    Bucket,
    ImportProject,
    ImportStorage,
    save_study_config,
)
from dae.parquet.parquet_writer import merge_variants_parquets
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.task_graph.graph import TaskGraph
from dae.utils import fs_utils
from impala_storage.schema1.impala_genotype_storage import ImpalaGenotypeStorage
from impala_storage.schema1.parquet_io import ParquetWriter
from impala_storage.schema1.parquet_io import (
    VariantsParquetWriter as S1VariantsWriter,
)

logger = logging.getLogger(__file__)


class ImpalaSchema1ImportStorage(ImportStorage):
    """Import logic for data in the Impala Schema 1 format."""

    @staticmethod
    def _pedigree_filename(project: ImportProject) -> str:
        return fs_utils.join(
            project.work_dir, f"{project.study_id}_pedigree",
            "pedigree.parquet")

    @staticmethod
    def _variants_dir(project: ImportProject) -> str:
        return fs_utils.join(project.work_dir, f"{project.study_id}_variants")

    @staticmethod
    def _get_partition_description(
        project: ImportProject,
        out_dir: Optional[str] = None,
    ) -> PartitionDescriptor:
        out_dir = out_dir if out_dir else project.work_dir
        return project.get_partition_descriptor()

    @classmethod
    def _do_write_pedigree(cls, project: ImportProject) -> None:
        start = time.time()
        ped_filename = cls._pedigree_filename(project)
        ParquetWriter.write_pedigree(
            ped_filename, project.get_pedigree(),
            cls._get_partition_description(project),
            S1VariantsWriter)
        elapsed = time.time() - start
        logger.info("prepare pedigree elapsed %.2f sec", elapsed)
        project.stats[("elapsed", "pedigree")] = elapsed

    @classmethod
    def _do_write_meta(cls, project: ImportProject) -> None:
        if not project.has_variants():
            return
        out_dir = cls._variants_dir(project)
        gpf_instance = project.get_gpf_instance()
        loader_type = next(iter(project.get_variant_loader_types()))
        gpf_instance = project.get_gpf_instance()
        variants_loader = project.get_variant_loader(
            loader_type=loader_type,
            reference_genome=gpf_instance.reference_genome)
        variants_loader = project.build_variants_loader_pipeline(
            variants_loader,
        )
        ParquetWriter.write_meta(
            out_dir,
            variants_loader,
            cls._get_partition_description(project),
            S1VariantsWriter)

    @classmethod
    def _do_write_variants(
        cls, project: ImportProject,
        bucket: Bucket,
    ) -> None:
        start = time.time()
        out_dir = cls._variants_dir(project)
        gpf_instance = project.get_gpf_instance()
        loader_type = next(iter(project.get_variant_loader_types()))
        variants_loader = project.get_variant_loader(
            bucket, loader_type, gpf_instance.reference_genome)
        variants_loader = project.build_variants_loader_pipeline(
            variants_loader,
        )
        ParquetWriter.write_variants(
            out_dir,
            variants_loader,
            cls._get_partition_description(project),
            bucket,
            project,
            S1VariantsWriter)
        elapsed = time.time() - start
        logger.info(
            "prepare variants for bucket %s elapsed %.2f sec",
            bucket, elapsed)
        project.stats[("elapsed", f"variants {bucket}")] = elapsed

    @classmethod
    def _variant_partitions(
        cls, project: ImportProject,
    ) -> Iterator[Tuple[str, List[Tuple[str, str]]]]:
        part_desc = cls._get_partition_description(project)
        chromosomes = project.get_variant_loader_chromosomes()
        chromosome_lengths = dict(filter(
            lambda cl: cl[0] in chromosomes,
            project.get_gpf_instance()
            .reference_genome
            .get_all_chrom_lengths()))
        _, fam_parts = \
            part_desc.get_variant_partitions(chromosome_lengths)
        for part in fam_parts:
            yield part_desc.partition_directory("", part), part

    @classmethod
    def _merge_parquets(
        cls, project: ImportProject, out_dir: str,
        partitions: List[Tuple[str, str]],
    ) -> None:
        full_out_dir = fs_utils.join(cls._variants_dir(project), out_dir)
        merge_variants_parquets(
            cls._get_partition_description(project),
            full_out_dir, partitions,
            parquet_version="1.0",
        )

    @classmethod
    def _do_load_in_hdfs(cls, project: ImportProject) -> None:
        start = time.time()
        genotype_storage = project.get_genotype_storage()
        if genotype_storage is None \
                or genotype_storage.storage_type != "impala":
            logger.error("missing or non-impala genotype storage")
            return

        partition_description = cls._get_partition_description(project)

        pedigree_file = cls._pedigree_filename(project)
        variants_dir = cls._variants_dir(project) \
            if project.has_variants() else None
        cast(ImpalaGenotypeStorage, genotype_storage).hdfs_upload_dataset(
            project.study_id,
            variants_dir,
            pedigree_file,
            partition_description)
        elapsed = time.time() - start
        logger.info("load in hdfs elapsed %.2f sec", elapsed)
        project.stats[("elapsed", "hdfs")] = elapsed

    @classmethod
    def _do_load_in_impala(cls, project: ImportProject) -> None:
        start = time.time()
        genotype_storage = project.get_genotype_storage()
        if genotype_storage is None \
                or genotype_storage.storage_type != "impala":
            logger.error("missing or non-impala genotype storage")
            return

        hdfs_variants_dir = \
            cast(ImpalaGenotypeStorage, genotype_storage) \
            .default_variants_hdfs_dirname(project.study_id)

        hdfs_pedigree_file = \
            cast(ImpalaGenotypeStorage, genotype_storage) \
            .default_pedigree_hdfs_filename(project.study_id)

        logger.info("HDFS variants dir: %s", hdfs_variants_dir)
        logger.info("HDFS pedigree file: %s", hdfs_pedigree_file)

        partition_description = cls._get_partition_description(project)

        if project.has_variants():
            variants_schema_fn = fs_utils.join(
                cls._variants_dir(project), "_VARIANTS_SCHEMA")
            with open(variants_schema_fn) as infile:
                content = infile.read()
                schema = toml.loads(content)
                variants_schema = schema["variants_schema"]
        else:
            hdfs_variants_dir = None
            variants_schema = None

        cast(ImpalaGenotypeStorage, genotype_storage).impala_import_dataset(
            project.study_id,
            hdfs_pedigree_file,
            hdfs_variants_dir,
            partition_description=partition_description,
            variants_schema=variants_schema)
        elapsed = time.time() - start
        logger.info("load in impala elapsed %.2f sec", elapsed)
        project.stats[("elapsed", "impala")] = elapsed

    @staticmethod
    def _construct_variants_table(study_id: str) -> str:
        return f"{study_id}_variants"

    @staticmethod
    def _construct_pedigree_table(study_id: str) -> str:
        return f"{study_id}_pedigree"

    @classmethod
    def _do_study_config(cls, project: ImportProject) -> None:
        start = time.time()
        pedigree_table = cls._construct_pedigree_table(project.study_id)
        variants_types = project.get_variant_loader_types()
        study_config = {
            "id": project.study_id,
            "conf_dir": ".",
            "has_denovo": project.has_denovo_variants(),
            "has_cnv": "cnv" in variants_types,
            "has_transmitted": bool({"dae", "vcf"} & variants_types),
            "genotype_storage": {
                "id": project.get_genotype_storage().storage_id,
                "tables": {"pedigree": pedigree_table},
            },
            "genotype_browser": {"enabled": False},
        }

        if project.has_variants():
            variants_table = cls._construct_variants_table(project.study_id)
            storage_config = study_config["genotype_storage"]
            storage_config["tables"][  # type: ignore
                "variants"] = variants_table
            study_config["genotype_browser"]["enabled"] = True  # type: ignore

        config_builder = StudyConfigBuilder(study_config)
        config = config_builder.build_config()

        save_study_config(
            project.get_gpf_instance().dae_config,
            project.study_id,
            config)
        elapsed = time.time() - start
        logger.info("study config elapsed %.2f sec", elapsed)
        project.stats[("elapsed", "study_config")] = elapsed

    def generate_import_task_graph(self, project: ImportProject) -> TaskGraph:
        graph = TaskGraph()

        pedigree_task = graph.create_task(
            "Generating Pedigree", self._do_write_pedigree, [project], [],
        )
        meta_task = graph.create_task(
            "Write Meta", self._do_write_meta, [project], [],
        )

        bucket_tasks = []
        for bucket in project.get_import_variants_buckets():
            task = graph.create_task(
                f"Converting Variants {bucket}", self._do_write_variants,
                [project, bucket], [],
            )
            bucket_tasks.append(task)

        # merge small parquet files into larger ones
        bucket_sync = graph.create_task(
            "Sync Parquet Generation", lambda: None, [], bucket_tasks,
        )
        output_dir_tasks = []
        for output_dir, partitions in self._variant_partitions(project):
            output_dir_tasks.append(graph.create_task(
                f"Merging {output_dir}", self._merge_parquets,
                [project, output_dir, partitions], [bucket_sync],
            ))

        # dummy task used for running the parquet generation w/o impala import
        all_parquet_task = graph.create_task(
            "Parquet Tasks", lambda: None, [], output_dir_tasks + [bucket_sync],
        )

        if project.has_genotype_storage():
            hdfs_task = graph.create_task(
                "Copying to HDFS", self._do_load_in_hdfs,
                [project], [pedigree_task, meta_task, all_parquet_task])

            impala_task = graph.create_task(
                "Importing into Impala", self._do_load_in_impala,
                [project], [hdfs_task])

            graph.create_task(
                "Creating a study config", self._do_study_config,
                [project], [impala_task])
        return graph
