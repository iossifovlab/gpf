import argparse
import os

from dae.annotation.annotate_utils import AnnotationTool
from dae.annotation.context import CLIAnnotationContext
from dae.annotation.parquet import (
    backup_schema2_study,
    produce_schema2_annotation_tasks,
    produce_schema2_merging_tasks,
    symlink_pedigree_and_family_variants,
    write_new_meta,
)
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.schema2_storage.schema2_import_storage import (
    create_schema2_dataset_layout,
)
from dae.task_graph.cli_tools import TaskGraphCli
from dae.variants_loaders.parquet.loader import ParquetLoader


class AnnotateSchema2ParquetTool(AnnotationTool):
    """Annotation tool for the Parquet file format."""

    def get_argument_parser(self) -> argparse.ArgumentParser:
        """Construct and configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Annotate Schema2 Parquet",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "input", default="-", nargs="?",
            help="the directory containing Parquet files")
        parser.add_argument(
            "-r", "--region",
            type=str, help="annotate only a specific region",
            default=None)
        parser.add_argument(
            "-s", "--region-size", default=300_000_000,
            type=int, help="region size to parallelize by")
        parser.add_argument(
            "-w", "--work-dir",
            help="Directory to store intermediate output files in",
            default="annotate_schema2_output")
        parser.add_argument(
            "-i", "--full-reannotation",
            help="Ignore any previous annotation and run "
            " a full reannotation.")
        output_behaviour = parser.add_mutually_exclusive_group()
        output_behaviour.add_argument(
            "-o", "--output",
            help="Path of the directory to hold the output")
        output_behaviour.add_argument(
            "-e", "--in-place",
            help="Produce output directly in given input dir.",
            action="store_true")
        output_behaviour.add_argument(
            "-m", "--meta",
            help="Print the input Parquet's meta properties.",
            action="store_true")

        CLIAnnotationContext.add_context_arguments(parser)
        TaskGraphCli.add_arguments(parser)
        VerbosityConfiguration.set_arguments(parser)
        return parser

    def print_meta(self) -> None:
        """Print the metadata of a Parquet study."""
        input_dir = os.path.abspath(self.args.input)
        if self.args.meta:
            loader = ParquetLoader.load_from_dir(input_dir)
            for k, v in loader.meta.items():
                print("=" * 50)
                print(k)
                print("=" * 50)
                print(v)
                print()

    def work(self) -> None:
        input_dir = os.path.abspath(self.args.input)

        if self.args.in_place:
            output_dir = input_dir
            input_layout = backup_schema2_study(input_dir)
            loader = ParquetLoader(input_layout)
        else:
            if not self.args.output:
                raise ValueError("No output path was provided!")
            output_dir = os.path.abspath(self.args.output)
            if os.path.exists(output_dir):
                raise ValueError(f"Output path '{output_dir}' already exists!")
            loader = ParquetLoader.load_from_dir(input_dir)

        output_layout = create_schema2_dataset_layout(output_dir)

        if loader.layout.summary is None:
            raise ValueError("Invalid summary dir in input layout!")
        if loader.layout.family is None:
            raise ValueError("Invalid family dir in input layout!")
        if output_layout.summary is None:
            raise ValueError("Invalid summary dir in output layout!")
        if output_layout.family is None:
            raise ValueError("Invalid family dir in output layout!")

        write_new_meta(loader, self.pipeline, output_layout)

        if not self.args.in_place:
            symlink_pedigree_and_family_variants(loader.layout, output_layout)

        annotation_tasks = produce_schema2_annotation_tasks(
            self.task_graph,
            loader,
            output_dir,
            self.pipeline.raw,
            self.grr,
            self.args.region_size,
            self.args.allow_repeated_attributes,
            region=self.args.region,
        )
        produce_schema2_merging_tasks(
            self.task_graph,
            annotation_tasks,
            loader,
            output_layout,
        )


def cli(
    raw_args: list[str] | None = None,
    gpf_instance: GPFInstance | None = None,
) -> None:
    """Entry method for AnnotateSchema2ParquetTool."""
    tool = AnnotateSchema2ParquetTool(raw_args, gpf_instance)
    if tool.args.meta:
        tool.print_meta()
        return
    tool.run()
