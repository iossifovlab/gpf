import argparse
import pathlib
from typing import Any

from dae.annotation.annotate_utils import AnnotationTool
from dae.annotation.context import CLIAnnotationContext
from dae.duckdb_storage.duckdb_genotype_storage import (
    DuckDbParquetStorage,
)
from dae.duckdb_storage.duckdb_storage_helpers import (
    PARQUET_SCAN,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.schema2_storage.schema2_import_storage import Schema2ImportStorage
from dae.studies.study import GenotypeData
from dae.task_graph.cli_tools import TaskGraphCli
from dae.utils.verbosity_configuration import VerbosityConfiguration


class ReannotateInstanceTool(AnnotationTool):
    """Annotation tool to reannotate the configured GPF instance"""

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
            default="annotate_schema2_output")
        parser.add_argument(
            "-n", "--dry-run",
            action="store_true",
            help="Output which studies will be reannotated"
                 " without carrying out the reannotation.",
        )
        # TODO Implement --full-reannotation after it is  # noqa: FIX002
        # implemented in annotate_schema2_parquet
        parser.add_argument(
            "-i", "--full-reannotation",
            help="Ignore any previous annotation and run "
                 " a full reannotation.",
        )

        CLIAnnotationContext.add_context_arguments(parser)
        TaskGraphCli.add_arguments(parser)
        VerbosityConfiguration.set_arguments(parser)
        return parser

    @staticmethod
    def _get_genotype_storage(
        study: GenotypeData,
        gpf_instance: GPFInstance,
    ) -> Any:
        if study.config.genotype_storage is None:
            genotype_storage_id = None
        else:
            genotype_storage_id = study.config.genotype_storage.id

        if genotype_storage_id is None:
            genotype_storage = \
                gpf_instance.genotype_storages.get_default_genotype_storage()
        else:
            genotype_storage = \
                gpf_instance.genotype_storages.get_genotype_storage(genotype_storage_id)
        return genotype_storage

    @staticmethod
    def _is_reannotatable(
        study: GenotypeData,
        gpf_instance: GPFInstance,
    ) -> bool:
        genotype_storage = ReannotateInstanceTool._get_genotype_storage(
            study, gpf_instance)

        return genotype_storage.storage_type in {"duckdb_parquet", "parquet"}

    @staticmethod
    def _get_parquet_dir(
        study: GenotypeData,
        gpf_instance: GPFInstance,
    ) -> str:
        genotype_storage = ReannotateInstanceTool._get_genotype_storage(
            study, gpf_instance)

        if not isinstance(genotype_storage, DuckDbParquetStorage):
            raise NotImplementedError

        summary_path = genotype_storage.build_study_layout(study.config).summary

        if summary_path is None:
            raise ValueError(f"No summary data in study {study.study_id}!")

        match = PARQUET_SCAN.fullmatch(summary_path)
        if match is None:
            raise ValueError(f"Invalid path to summary data {summary_path}!")

        return str(
            pathlib.Path(match.groupdict()["parquet_path"]).parent.parent)

    def work(self) -> None:
        if self.gpf_instance is None:
            raise ValueError("No configured GPF instance to work with!")
        reannotatable_data: list[GenotypeData] = [
            study
            for study in self.gpf_instance.get_all_genotype_data()
            if self._is_reannotatable(study, self.gpf_instance)
        ]
        # TODO When constructing reannotatable_data, maybe for  # noqa: FIX002
        # each study we could check the contents of the constructed
        # ReannotationPipeline? so for studies with empty ReannotationPipelines
        # (i.e. no reannotation needed) they would not be displayed
        print("Studies to be reannotated:")
        for study in reannotatable_data:
            print(f"-> {study.study_id}")
        if self.args.dry_run:
            return

        for study in reannotatable_data:
            print(f"Processing {study.study_id}...")
            study_dir = self._get_parquet_dir(study, self.gpf_instance)
            graph = Schema2ImportStorage.generate_reannotate_task_graph(
                self.gpf_instance, study_dir,
                self.args.region_size, self.args.allow_repeated_attributes,
            )
            TaskGraphCli.process_graph(graph, **vars(self.args))


def cli(
    raw_args: list[str] | None = None,
    gpf_instance: GPFInstance | None = None,
) -> None:
    """Entry point method for instance reannotation tool."""
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()
    tool = ReannotateInstanceTool(raw_args, gpf_instance)
    tool.run()