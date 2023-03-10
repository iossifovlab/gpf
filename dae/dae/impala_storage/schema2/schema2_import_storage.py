import logging
from typing import cast

from dae.utils import fs_utils
from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.impala_storage.schema1.import_commons import save_study_config
from dae.import_tools.import_tools import ImportStorage
from dae.task_graph.graph import TaskGraph
from dae.impala_storage.schema2.schema2_genotype_storage import \
    Schema2GenotypeStorage
from dae.parquet.parquet_writer import ParquetWriter
from dae.parquet.schema2.parquet_io import \
    VariantsParquetWriter as S2VariantsWriter
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet import helpers as parquet_helpers


logger = logging.getLogger(__file__)


class Schema2ImportStorage(ImportStorage):
    """Import logic for data in the Impala Schema 1 format."""

    @staticmethod
    def _pedigree_dir(project):
        return fs_utils.join(project.work_dir, f"{project.study_id}_pedigree")

    @staticmethod
    def _variants_dir(project):
        return fs_utils.join(project.work_dir, f"{project.study_id}_variants")

    @classmethod
    def _meta_dir(cls, project):
        return cls._variants_dir(project)

    @staticmethod
    def _get_partition_description(project, out_dir=None):
        out_dir = out_dir if out_dir else project.work_dir
        config_dict = project.get_partition_description_dict()

        if config_dict is None:
            return PartitionDescriptor()
        return PartitionDescriptor.parse_dict(config_dict)

    @classmethod
    def _do_write_pedigree(cls, project):
        out_dir = cls._pedigree_dir(project)
        ParquetWriter.write_pedigree(
            out_dir, project.get_pedigree(),
            cls._get_partition_description(project))

    @classmethod
    def _do_write_variant(cls, project, bucket):
        out_dir = cls._variants_dir(project)
        gpf_instance = project.get_gpf_instance()
        ParquetWriter.write_variants(
            out_dir,
            project.get_variant_loader(
                bucket, gpf_instance.reference_genome),
            cls._get_partition_description(project),
            bucket,
            project,
            S2VariantsWriter)

    @classmethod
    def _variant_partitions(cls, project):
        part_desc = cls._get_partition_description(project)
        chromosome_lengths = dict(
            project.get_gpf_instance().reference_genome.get_all_chrom_lengths()
        )
        sum_parts, fam_parts = \
            part_desc.get_variant_partitions(chromosome_lengths)
        for part in sum_parts:
            yield part_desc.partition_directory("summary", part), part
        for part in fam_parts:
            yield part_desc.partition_directory("family", part), part

    @classmethod
    def _merge_parquets(cls, project, out_dir, partitions):
        full_out_dir = fs_utils.join(cls._variants_dir(project), out_dir)
        output_parquet_file = fs_utils.join(
            full_out_dir,
            cls._get_partition_description(project)
               .partition_filename("merged", partitions, bucket_index=None)
        )
        parquet_files = fs_utils.glob(
            fs_utils.join(full_out_dir, "*.parquet")
        )

        is_output_in_input = \
            any(fn.endswith(output_parquet_file) for fn in parquet_files)
        if is_output_in_input:
            # a leftover file from a previous run. Remove from list of files.
            # we use endswith instead of == because of path normalization
            for i, filename in enumerate(parquet_files):
                if filename.endswith(output_parquet_file):
                    parquet_files.pop(i)
                    break

        if len(parquet_files) > 1:
            logger.info(
                "Merging %d files in %s", len(parquet_files), full_out_dir
            )
            parquet_helpers.merge_parquets(parquet_files, output_parquet_file)

    @classmethod
    def _do_load_in_hdfs(cls, project):
        genotype_storage = project.get_genotype_storage()
        assert isinstance(genotype_storage, Schema2GenotypeStorage)

        pedigree_file = fs_utils.join(cls._pedigree_dir(project),
                                      "pedigree.parquet")
        meta_file = fs_utils.join(cls._meta_dir(project), "meta.parquet")
        return genotype_storage.hdfs_upload_dataset(
            project.study_id,
            cls._variants_dir(project),
            pedigree_file,
            meta_file)

    @classmethod
    def _do_load_in_impala(cls, project, hdfs_study_layout):
        genotype_storage = project.get_genotype_storage()
        assert isinstance(genotype_storage, Schema2GenotypeStorage)

        logger.info("HDFS study layout: %s", hdfs_study_layout)

        partition_description = cls._get_partition_description(project)
        genotype_storage.import_dataset(
            project.study_id,
            hdfs_study_layout,
            partition_description=partition_description,
        )

    @classmethod
    def _do_study_config(cls, project):
        genotype_storage: Schema2GenotypeStorage = \
            cast(Schema2GenotypeStorage, project.get_genotype_storage())
        # pylint: disable=protected-access
        pedigree_table = genotype_storage\
            ._construct_pedigree_table(project.study_id)
        summary_table, family_table = genotype_storage\
            ._construct_variant_tables(project.study_id)
        meta_table = genotype_storage\
            ._construct_metadata_table(project.study_id)

        variants_types = project.get_import_variants_types()
        study_config = {
            "id": project.study_id,
            "conf_dir": ".",
            "has_denovo": "denovo" in variants_types,
            "has_cnv": "cnv" in variants_types,
            "has_transmitted": bool({"dae", "vcf"} & variants_types),
            "genotype_storage": {
                "id": genotype_storage.storage_id,
                "tables": {"pedigree": pedigree_table},
            },
            "genotype_browser": {"enabled": False},
        }

        if summary_table:
            assert family_table is not None
            storage_config = study_config["genotype_storage"]
            storage_config["tables"]["summary"] = summary_table
            storage_config["tables"]["family"] = family_table
            storage_config["tables"]["meta"] = meta_table
            study_config["genotype_browser"]["enabled"] = True

        config_builder = StudyConfigBuilder(study_config)
        config = config_builder.build_config()

        save_study_config(
            project.get_gpf_instance().dae_config,
            project.study_id,
            config, force=True)

    def generate_import_task_graph(self, project) -> TaskGraph:
        graph = TaskGraph()

        pedigree_task = graph.create_task(
            "Generating Pedigree", self._do_write_pedigree, [project], [],
            input_files=[project.get_pedigree_filename()]
        )

        bucket_tasks = []
        for bucket in project.get_import_variants_buckets():
            task = graph.create_task(
                f"Converting Variants {bucket}", self._do_write_variant,
                [project, bucket], [],
                input_files=project.get_input_filenames(bucket)
            )
            bucket_tasks.append(task)

        # merge small parquet files into larger ones
        bucket_sync = graph.create_task(
            "Sync Parquet Generation", lambda: None, [], bucket_tasks
        )
        output_dir_tasks = []
        for output_dir, partitions in self._variant_partitions(project):
            output_dir_tasks.append(graph.create_task(
                f"Merging {output_dir}", self._merge_parquets,
                [project, output_dir, partitions], [bucket_sync]
            ))

        # dummy task used for running the parquet generation w/o impala import
        all_parquet_task = graph.create_task(
            "Parquet Tasks", lambda: None, [], output_dir_tasks + [bucket_sync]
        )

        if project.has_genotype_storage():
            hdfs_task = graph.create_task(
                "Copying to HDFS", self._do_load_in_hdfs,
                [project], [pedigree_task, all_parquet_task])

            impala_task = graph.create_task(
                "Importing into Impala", self._do_load_in_impala,
                [project, hdfs_task], [hdfs_task])
            graph.create_task(
                "Creating a study config", self._do_study_config,
                [project], [impala_task])

        return graph
