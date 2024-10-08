import logging
import os
import shutil
from typing import Any

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.import_tools.import_tools import (
    ImportProject,
    ImportStorage,
    save_study_config,
)
from dae.task_graph.graph import TaskGraph
from dae.variants_loaders.raw.loader import (
    StoredAnnotationDecorator,
    VariantsGenotypesLoader,
    VariantsLoader,
)

logger = logging.getLogger(__file__)


class InmemoryImportStorage(ImportStorage):
    """Defines import storage for in-memory genotype storage."""

    @staticmethod
    def _get_destination_study_dir(project: ImportProject) -> str:
        genotype_storage = project.get_genotype_storage()
        storage_config = genotype_storage.storage_config
        storage_data_dir: str = storage_config["dir"]
        if not os.path.isabs(storage_data_dir):
            raise ValueError(
                f"filesystem storage data directory should be an absolute "
                f"path, but is not: {storage_data_dir}")
        destination_dir = os.path.join(storage_data_dir, project.study_id)
        os.makedirs(destination_dir, exist_ok=True)
        return destination_dir

    @classmethod
    def _copy_to_filesystem_storage(
            cls, project: ImportProject, source_filename: str) -> str:
        destination_dir = cls._get_destination_study_dir(project)
        destination_filename = os.path.join(
            destination_dir, os.path.basename(source_filename))
        shutil.copyfile(source_filename, destination_filename)
        return destination_filename

    @classmethod
    def _do_copy_pedigree(
            cls, project: ImportProject) -> dict[str, Any]:
        genotype_storage = project.get_genotype_storage()
        if genotype_storage.read_only:
            raise OSError(
                f"genotype storage is read-only: "
                f"{genotype_storage.storage_id}")

        pedigree_filename, pedigree_params = project.get_pedigree_params()
        dest_filename = cls._copy_to_filesystem_storage(
            project, pedigree_filename)
        return {
            "path": dest_filename,
            "params": pedigree_params,
        }

    @classmethod
    def _decorate_variants_loader(
        cls, project: ImportProject,
        variants_loader: VariantsGenotypesLoader,
    ) -> VariantsLoader:
        result_loader = project.build_variants_loader_pipeline(
            variants_loader)
        return result_loader

    @classmethod
    def _do_copy_variants(
            cls, project: ImportProject,
            loader_type: str | None = None) -> list[dict[str, Any]]:
        genotype_storage = project.get_genotype_storage()
        if genotype_storage.read_only:
            raise OSError(
                f"genotype storage is read-only: "
                f"{genotype_storage.storage_id}")

        if loader_type is None:
            loader_types = project.get_variant_loader_types()
        else:
            loader_types = set([loader_type])

        destination_dir = cls._get_destination_study_dir(project)

        def construct_destination_filename(fname: str) -> str:
            return os.path.join(
                destination_dir, os.path.basename(fname))

        variants_config = []
        for variants_type in loader_types:
            variants_loader = project.get_variant_loader(
                loader_type=variants_type)

            dest_filenames = []
            for source_filename in variants_loader.filenames:
                dest = cls._copy_to_filesystem_storage(
                    project, source_filename)
                dest_filenames.append(dest)
                if os.path.exists(f"{source_filename}.tbi"):
                    cls._copy_to_filesystem_storage(
                        project, f"{source_filename}.tbi")

            annotation_filename = StoredAnnotationDecorator\
                .build_annotation_filename(dest_filenames[0])
            StoredAnnotationDecorator.save_annotation_file(
                cls._decorate_variants_loader(
                    project, variants_loader),  # type: ignore
                annotation_filename)

            config_filenames = list(map(
                construct_destination_filename,
                variants_loader.variants_filenames))
            variants_config.append({
                "path": " ".join(config_filenames),  # FIXME: switch to list
                "params": variants_loader.build_arguments_dict(),
                "format": variants_type,
            })
        return variants_config

    @classmethod
    def _do_study_import(cls, project: ImportProject) -> None:
        genotype_storage = project.get_genotype_storage()
        if genotype_storage.read_only:
            raise OSError(
                f"genotype storage is read-only: "
                f"{genotype_storage.storage_id}")
        pedigree_config = cls._do_copy_pedigree(project)
        variants_config = cls._do_copy_variants(project)
        variants_types = project.get_variant_loader_types()
        config = {
            "id": project.study_id,
            "has_denovo": project.has_denovo_variants(),
            "has_cnv": "cnv" in variants_types,
            "has_transmitted": bool({"dae", "vcf"} & variants_types),
            "genotype_storage": {
                "id": project.get_genotype_storage().storage_id,
                "files": {
                    "pedigree": pedigree_config,
                    "variants": variants_config,
                },
            },
        }
        config_builder = StudyConfigBuilder(config)
        study_config = config_builder.build_config()

        save_study_config(
            project.get_gpf_instance().dae_config,
            project.study_id,
            study_config)

    def generate_import_task_graph(self, project: ImportProject) -> TaskGraph:
        graph = TaskGraph()
        graph.create_task(
            "study import", self._do_study_import,
            [project], [])

        return graph
