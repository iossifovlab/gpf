import argparse
import logging
import os
import pathlib
import sys
from typing import Any, cast

from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.duckdb_storage.duckdb2_variants import DuckDb2Variants
from dae.duckdb_storage.duckdb_genotype_storage import (
    DuckDbParquetStorage,
)
from dae.duckdb_storage.duckdb_storage_helpers import (
    PARQUET_SCAN,
)
from dae.genomic_resources.genomic_context import (
    context_providers_add_argparser_arguments,
    context_providers_init,
    get_genomic_context,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.parquet_storage.storage import ParquetLoaderVariants
from dae.schema2_storage.schema2_import_storage import Schema2ImportStorage
from dae.studies.study import GenotypeData, GenotypeDataStudy
from dae.task_graph.cli_tools import TaskGraphCli
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger(__name__)


class ReannotateInstanceTool:
    """Annotation tool to reannotate the configured GPF instance"""

    def __init__(
        self,
        raw_args: list[str] | None = None, *,
        gpf_instance: GPFInstance | None = None,
    ) -> None:
        if not raw_args:
            raw_args = sys.argv[1:]
        parser = self.get_argument_parser()
        self.args = parser.parse_args(raw_args)
        context_providers_init(**vars(self.args), gpf_instance=gpf_instance)

        self.genomic_context = get_genomic_context()
        self.gpf_instance = cast(
            GPFInstance,
            self.genomic_context.get_context_object("gpf_instance"))
        if not isinstance(self.gpf_instance, GPFInstance):
            raise TypeError("No valid GPF instance configured!")
        VerbosityConfiguration.set(self.args)

    def get_argument_parser(self) -> argparse.ArgumentParser:
        """Construct and configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Reannotate instance",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "-r", "--region-size", default=300_000_000,
            type=int, help="region size to parallelize by",
        )
        parser.add_argument(
            "-w", "--work-dir",
            help="Directory to store intermediate output files in",
            default=".reannotate-instance")
        parser.add_argument(
            "-n", "--dry-run",
            action="store_true",
            help="Output which studies will be reannotated"
                 " without carrying out the reannotation.",
        )

        context_providers_add_argparser_arguments(parser)

        parser.add_argument(
            "--full-reannotation", "--fr",
            help="Ignore any previous annotation and run "
                 " a full reannotation.",
            action="store_true",
        )

        TaskGraphCli.add_arguments(parser)
        VerbosityConfiguration.set_arguments(parser)
        return parser

    @staticmethod
    def _get_genotype_storage(
        study: GenotypeData,
        gpf_instance: GPFInstance,
    ) -> Any:
        if study.config["genotype_storage"] is None:
            genotype_storage_id = None
        else:
            genotype_storage_id = study.config["genotype_storage"]["id"]

        if genotype_storage_id is None:
            genotype_storage = \
                gpf_instance.genotype_storages.get_default_genotype_storage()
        else:
            genotype_storage = \
                gpf_instance.genotype_storages.get_genotype_storage(
                    genotype_storage_id)
        return genotype_storage

    @staticmethod
    def _is_study_annotation_up_to_date(
        study_id: str,
        gpf_instance: GPFInstance,
    ) -> bool:
        canonical = set(gpf_instance.get_annotation_pipeline().get_info())
        study = gpf_instance.get_genotype_data(study_id)
        assert study is not None
        assert not study.is_group
        study = cast(GenotypeDataStudy, study)
        storage = gpf_instance.genotype_storages.get_genotype_storage(
            study.config["genotype_storage"]["id"],
        )
        backend = study.backend
        if storage.storage_type == "duckdb_parquet":
            raw = cast(DuckDb2Variants, backend).fetch_annotation()
        elif storage.storage_type == "parquet":
            meta = cast(ParquetLoaderVariants, backend).loader.meta
            raw = meta["annotation_pipeline"]
        else:
            raise ValueError(f"Invalid storage type {storage.storage_type}")
        raw = raw.strip()
        annotation = load_pipeline_from_yaml(raw, gpf_instance.grr)
        new_infos = set(annotation.get_info())
        return new_infos == canonical

    @staticmethod
    def _is_reannotatable(
        study: GenotypeData,
        gpf_instance: GPFInstance,
    ) -> bool:
        genotype_storage = ReannotateInstanceTool._get_genotype_storage(
            study, gpf_instance)
        annotation_ok = ReannotateInstanceTool._is_study_annotation_up_to_date(
            study.study_id, gpf_instance)
        return genotype_storage.storage_type in {"duckdb_parquet", "parquet"} \
            and not annotation_ok

    @staticmethod
    def _get_parquet_dir(
        study: GenotypeData,
        gpf_instance: GPFInstance,
    ) -> str:
        genotype_storage = ReannotateInstanceTool._get_genotype_storage(
            study, gpf_instance)

        if not isinstance(genotype_storage, DuckDbParquetStorage):
            raise NotImplementedError

        summary_path = genotype_storage\
            .build_study_layout(study.config).summary

        if summary_path is None:
            raise ValueError(f"No summary data in study {study.study_id}!")

        match = PARQUET_SCAN.fullmatch(summary_path)
        if match is None:
            raise ValueError(f"Invalid path to summary data {summary_path}!")

        path = pathlib.Path(match.groupdict()["parquet_path"])
        while path.name != "summary":
            path = path.parent
        return str(path.parent)

    def run(self) -> None:
        """Run the tool."""
        if self.gpf_instance is None:
            raise ValueError("No configured GPF instance to work with!")
        reannotatable_data: list[GenotypeData] = [
            study
            for study in self.gpf_instance.get_all_genotype_data()
            if (not study.is_group
                and not study.is_remote
                and self._is_reannotatable(study, self.gpf_instance))
        ]

        if not reannotatable_data:
            logger.info("Nothing to be done.")
            return

        print("Studies to be reannotated:")
        for study in reannotatable_data:
            print(f"-> {study.study_id}")

        if self.args.dry_run:
            return

        for study in reannotatable_data:
            task_status_dir = os.path.join(
                self.args.work_dir, ".task-progress", study.study_id)
            task_log_dir = os.path.join(
                self.args.work_dir, ".task-log", study.study_id)
            pipeline_work_dir = pathlib.Path(
                self.args.work_dir, "work", study.study_id)
            study_dir = self._get_parquet_dir(study, self.gpf_instance)
            graph = Schema2ImportStorage.generate_reannotate_task_graph(
                self.gpf_instance, study_dir,
                self.args.region_size,
                pipeline_work_dir,
                allow_repeated_attributes=self.args.allow_repeated_attributes,
                full_reannotation=self.args.full_reannotation,
            )
            kwargs = {**vars(self.args),
                      "task_status_dir": task_status_dir,
                      "task_log_dir": task_log_dir}
            TaskGraphCli.process_graph(graph, **kwargs)


def cli(
    raw_args: list[str] | None = None,
) -> None:
    """Entry point method for instance reannotation tool."""
    tool = ReannotateInstanceTool(raw_args)
    tool.run()
