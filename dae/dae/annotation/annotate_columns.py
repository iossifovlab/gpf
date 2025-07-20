from __future__ import annotations

import argparse
import logging
import os
import sys
from contextlib import closing
from pathlib import Path
from typing import Any

from pysam import TabixFile

from dae.annotation.annotate_utils import (
    AnnotationTool,
    produce_partfile_paths,
    produce_regions,
    produce_tabix_index,
)
from dae.annotation.annotation_config import (
    RawPipelineConfig,
)
from dae.annotation.format_handlers import ColumnsFormat
from dae.annotation.genomic_context import CLIAnnotationContextProvider
from dae.annotation.record_to_annotatable import (
    add_record_to_annotable_arguments,
)
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.task_graph import TaskGraphCli
from dae.utils.fs_utils import tabix_index_filename

logger = logging.getLogger("annotate_columns")


def concat(partfile_paths: list[str], output_path: str) -> None:
    """Concatenate multiple DSV files into a single DSV file *in order*."""
    # Get any header from the partfiles, they should all be equal
    # and usable as a final output header
    header = Path(partfile_paths[0]).read_text().split("\n")[0]

    with open(output_path, "w") as outfile:
        outfile.write(header)
        for path in partfile_paths:
            # newline to separate from previous content
            outfile.write("\n")
            # read partfile content
            partfile_content = Path(path).read_text().strip("\r\n")
            # remove header from content
            partfile_content = "\n".join(partfile_content.split("\n")[1:])
            # write to output
            outfile.write(partfile_content)
        outfile.write("\n")

    for partfile_path in partfile_paths:
        os.remove(partfile_path)


class AnnotateColumnsTool(AnnotationTool):
    """Annotation tool for TSV-style text files."""

    def __init__(
        self,
        raw_args: list[str] | None = None,
    ) -> None:
        super().__init__(raw_args)
        self.output: str | None = None
        self.ref_genome_id: str | None = None

    def get_argument_parser(self) -> argparse.ArgumentParser:
        """Configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Annotate columns",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "input", default="-", nargs="?",
            help="the input column file")
        parser.add_argument(
            "-r", "--region-size", default=300_000_000,
            type=int, help="region size to parallelize by")
        parser.add_argument(
            "-w", "--work-dir",
            help="Directory to store intermediate output files in",
            default="annotate_columns_output")
        parser.add_argument(
            "-o", "--output",
            help="Filename of the output result",
            default=None)
        parser.add_argument(
            "-in-sep", "--input-separator", default="\t",
            help="The column separator in the input")
        parser.add_argument(
            "-out-sep", "--output-separator", default="\t",
            help="The column separator in the output")
        parser.add_argument(
            "--reannotate", default=None,
            help="Old pipeline config to reannotate over")
        parser.add_argument(
            "-i", "--full-reannotation",
            help="Ignore any previous annotation and run "
            " a full reannotation.",
            action="store_true",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=0,  # 0 = annotate iteratively, no batches
            help="Annotate in batches of",
        )

        CLIAnnotationContextProvider.add_argparser_arguments(parser)
        add_record_to_annotable_arguments(parser)
        TaskGraphCli.add_arguments(parser)
        VerbosityConfiguration.set_arguments(parser)
        return parser

    def prepare_for_annotation(self) -> None:
        if self.args.output:
            self.output = self.args.output.rstrip(".gz")
        else:
            input_name = self.args.input.rstrip(".gz")
            if "." in input_name:
                idx = input_name.find(".")
                self.output = f"{input_name[:idx]}_annotated{input_name[idx:]}"
            else:
                self.output = f"{input_name}_annotated"
        ref_genome = self.context.get_reference_genome()
        self.ref_genome_id = ref_genome.resource_id \
            if ref_genome is not None else None

    def add_tasks_to_graph(self) -> None:
        assert self.output is not None
        pipeline_config_old = None
        if self.args.reannotate:
            pipeline_config_old = Path(self.args.reannotate).read_text()

        if tabix_index_filename(self.args.input):
            with closing(TabixFile(self.args.input)) as pysam_file:
                regions = produce_regions(pysam_file, self.args.region_size)
            file_paths = produce_partfile_paths(
                self.args.input, regions, self.args.work_dir)

            region_tasks = []
            for region, path in zip(regions, file_paths, strict=True):
                task_id = f"part-{str(region).replace(':', '-')}"

                handler = ColumnsFormat(
                    self.pipeline.raw,
                    pipeline_config_old,
                    vars(self.args),
                    self.grr.definition,
                    region,
                    self.args.input,
                    path,
                    self.ref_genome_id,
                )

                region_tasks.append(self.task_graph.create_task(
                    task_id,
                    AnnotateColumnsTool.annotate,
                    args=[handler, self.args.batch_size > 0],
                    deps=[]))

            concat_task = self.task_graph.create_task(
                "concat",
                concat,
                args=[
                    file_paths,
                    self.output,
                ],
                deps=region_tasks)

            self.task_graph.create_task(
                "compress_and_tabix",
                produce_tabix_index,
                args=[self.output, self.args],
                deps=[concat_task])
        else:
            handler = ColumnsFormat(
                self.pipeline.raw,
                pipeline_config_old,
                vars(self.args),
                self.grr.definition,
                None,
                self.args.input,
                self.output,
                self.ref_genome_id,
            )
            self.task_graph.create_task(
                "annotate_all",
                AnnotateColumnsTool.annotate,
                args=[handler, self.args.batch_size > 0],
                deps=[])


def cli(raw_args: list[str] | None = None) -> None:
    tool = AnnotateColumnsTool(raw_args)
    tool.run()


if __name__ == "__main__":
    cli(sys.argv[1:])
