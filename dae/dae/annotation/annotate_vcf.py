from __future__ import annotations

import argparse
import logging
import os
import sys
from contextlib import closing
from pathlib import Path

from pysam import (
    TabixFile,
    VariantFile,
)

from dae.annotation.annotate_utils import (
    AnnotationTool,
    produce_partfile_paths,
    produce_regions,
    produce_tabix_index,
)
from dae.annotation.annotation_config import (
    RawAnnotatorsConfig,
)
from dae.annotation.context import CLIAnnotationContext
from dae.annotation.format_handlers import VCFFormat
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.task_graph import TaskGraphCli
from dae.utils.fs_utils import tabix_index_filename
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("annotate_vcf")


def combine(
    args,
    input_file_path: str,
    pipeline_config: RawAnnotatorsConfig,
    pipeline_config_old: str | None,
    grr_definition: dict | None,
    partfile_paths: list[str],
    output_file_path: str,
) -> None:
    """Combine annotated region parts into a single VCF file."""

    output_handler = VCFFormat(
        pipeline_config,
        pipeline_config_old,
        vars(args),
        grr_definition,
        None,
        input_file_path,
        output_file_path.rstrip(".gz"),
    )

    output_handler.open()
    assert output_handler.output_file is not None
    for partfile_path in partfile_paths:
        with VariantFile(partfile_path) as partfile:
            for rec in partfile.fetch():
                output_handler.output_file.write(rec)
    output_handler.close()

    for partfile_path in partfile_paths:
        os.remove(partfile_path)


class AnnotateVCFTool(AnnotationTool):
    """Annotation tool for the VCF file format."""

    def __init__(
        self, raw_args: list[str] | None = None,
        gpf_instance: GPFInstance | None = None,
    ):
        super().__init__(raw_args, gpf_instance)
        self.output = None

    def get_argument_parser(self) -> argparse.ArgumentParser:
        """Construct and configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Annotate VCF",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument("input", default="-", nargs="?",
                            help="the input vcf file")
        parser.add_argument("-r", "--region-size", default=300_000_000,
                            type=int, help="region size to parallelize by")
        parser.add_argument("-w", "--work-dir",
                            help="Directory to store intermediate output files",
                            default="annotate_vcf_output")
        parser.add_argument("-o", "--output",
                            help="Filename of the output VCF result",
                            default=None)
        parser.add_argument("--reannotate", default=None,
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

        CLIAnnotationContext.add_context_arguments(parser)
        TaskGraphCli.add_arguments(parser)
        VerbosityConfiguration.set_arguments(parser)
        return parser

    def prepare_for_annotation(self) -> None:
        if self.args.output:
            self.output = self.args.output
        else:
            self.output = os.path.basename(
                self.args.input).split(".")[0] + "_annotated.vcf"

    def add_tasks_to_graph(self) -> None:
        assert self.grr is not None
        assert self.output is not None
        pipeline_config_old = None
        if self.args.reannotate:
            pipeline_config_old = Path(self.args.reannotate).read_text()

        if not tabix_index_filename(self.args.input):
            handler = VCFFormat(
                self.pipeline.raw,
                pipeline_config_old,
                vars(self.args),
                self.grr.definition,
                None,
                self.args.input,
                self.output,
            )
            self.task_graph.create_task(
                "all_variants_annotate",
                AnnotateVCFTool.annotate,
                [handler, self.args.batch_size > 0],
                [],
            )
        else:
            with closing(TabixFile(self.args.input)) as pysam_file:
                regions = produce_regions(pysam_file, self.args.region_size)
            file_paths = produce_partfile_paths(
                self.args.input, regions, self.args.work_dir)
            region_tasks = []
            for index, (region, file_path) in enumerate(
                zip(regions, file_paths, strict=True),
            ):
                handler = VCFFormat(
                    self.pipeline.raw,
                    pipeline_config_old,
                    vars(self.args),
                    self.grr.definition,
                    region,
                    self.args.input,
                    file_path,
                )
                assert self.grr is not None
                region_tasks.append(self.task_graph.create_task(
                    f"part-{index}",
                    AnnotateVCFTool.annotate,
                    [handler, self.args.batch_size > 0],
                    [],
                ))

            assert self.grr is not None
            combine_task = self.task_graph.create_task(
                "combine",
                combine,
                [self.args,
                 self.args.input,
                 self.pipeline.raw,
                 pipeline_config_old,
                 self.grr.definition,
                 file_paths,
                 self.output],
                region_tasks,
            )
            self.task_graph.create_task(
                "compress_and_tabix",
                produce_tabix_index,
                [self.output],
                [combine_task])


def cli(raw_args: list[str] | None = None) -> None:
    tool = AnnotateVCFTool(raw_args)
    tool.run()


if __name__ == "__main__":
    cli(sys.argv[1:])
