import logging
from typing import cast

from dae.utils import fs_utils
from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.impala_storage.schema1.import_commons import save_study_config
from dae.parquet.parquet_writer import ParquetWriter
from dae.import_tools.import_tools import ImportStorage
from dae.task_graph.graph import TaskGraph
from dae.parquet.schema2.parquet_io import NoPartitionDescriptor, \
    ParquetManager, ParquetPartitionDescriptor


from gcp_genotype_storage.gcp_genotype_storage import GcpStudyLayout, \
    GcpGenotypeStorage


logger = logging.getLogger(__file__)


class GcpImportStorage(ImportStorage):
    """Import logic for data in the GCP Schema 2."""

    @staticmethod
    def _pedigree_dir(project):
        return fs_utils.join(
            project.work_dir, f"{project.study_id}_pedigree")

    @staticmethod
    def _variants_dir(project):
        return fs_utils.join(project.work_dir, f"{project.study_id}_variants")

    @classmethod
    def _pedigree_path(cls, project):
        return fs_utils.join(
            cls._pedigree_dir(project), "pedigree.parquet")

    @classmethod
    def _summary_variants_path(cls, project):
        return fs_utils.join(cls._variants_dir(project), "summary")

    @classmethod
    def _family_variants_path(cls, project):
        return fs_utils.join(cls._variants_dir(project), "family")

    @classmethod
    def _meta_path(cls, project):
        return fs_utils.join(cls._variants_dir(project), "meta.parquet")

    @staticmethod
    def _get_partition_description(project, out_dir=None):
        out_dir = out_dir if out_dir else project.work_dir
        config_dict = project.get_partition_description_dict()
        if config_dict is None:
            return NoPartitionDescriptor(out_dir)
        return ParquetPartitionDescriptor.from_dict(config_dict, out_dir)

    @classmethod
    def _do_write_pedigree(cls, project):
        out_dir = cls._pedigree_dir(project)
        ParquetWriter.write_pedigree(
            project.get_pedigree(), out_dir,
            cls._get_partition_description(project),
            ParquetManager(),
        )

    @classmethod
    def _do_write_variant(cls, project, bucket):
        out_dir = cls._variants_dir(project)
        gpf_instance = project.get_gpf_instance()
        ParquetWriter.write_variant(
            project.get_variant_loader(bucket,
                                       gpf_instance.reference_genome),
            bucket,
            gpf_instance,
            project, cls._get_partition_description(project, out_dir),
            ParquetManager())

    @classmethod
    def _do_import_dataset(cls, project):
        parquet_data_layout = GcpStudyLayout(
            cls._pedigree_path(project),
            cls._summary_variants_path(project),
            cls._family_variants_path(project),
            cls._meta_path(project)
        )
        genotype_storage = cast(
            GcpGenotypeStorage, project.get_genotype_storage())
        assert isinstance(genotype_storage, GcpGenotypeStorage)
        genotype_storage.gcp_import_dataset(
            project.study_id, parquet_data_layout)

    @classmethod
    def _do_study_config(cls, project):
        genotype_storage: GcpGenotypeStorage = \
            cast(GcpGenotypeStorage, project.get_genotype_storage())
        # pylint: disable=protected-access
        study_tables = genotype_storage._study_tables({"id": project.study_id})

        variants_types = project.get_import_variants_types()
        study_config = {
            "id": project.study_id,
            "conf_dir": ".",
            "has_denovo": "denovo" in variants_types,
            "has_cnv": "cnv" in variants_types,
            "has_transmitted": bool({"dae", "vcf"} & variants_types),
            "genotype_storage": {
                "id": genotype_storage.storage_id,
                "tables": {"pedigree": study_tables.pedigree},
            },
            "genotype_browser": {"enabled": False},
        }

        if study_tables.summary_variants:
            assert study_tables.family_variants is not None
            storage_config = study_config["genotype_storage"]
            storage_config["tables"]["summary"] = study_tables.summary_variants
            storage_config["tables"]["family"] = study_tables.summary_variants
            storage_config["tables"]["meta"] = study_tables.meta
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

        import_task = graph.create_task(
            "Import Dataset into GCP genotype storage",
            self._do_import_dataset,
            [project], [pedigree_task, *bucket_tasks])

        graph.create_task(
            "Create study config",
            self._do_study_config,
            [project], [import_task])
        return graph
