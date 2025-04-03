from __future__ import annotations

import argparse
import gzip
import logging
import os
import sys
from collections.abc import Generator
from contextlib import closing
from pathlib import Path
from typing import Any, cast

from pysam import TabixFile

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotate_utils import (
    AbstractFormat,
    AnnotationTool,
    produce_partfile_paths,
    produce_regions,
    produce_tabix_index,
    stringify,
)
from dae.annotation.annotation_config import (
    RawPipelineConfig,
)
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import (
    ReannotationPipeline,
)
from dae.annotation.context import CLIAnnotationContext
from dae.annotation.record_to_annotatable import (
    add_record_to_annotable_arguments,
    build_record_to_annotatable,
)
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.task_graph import TaskGraphCli
from dae.utils.fs_utils import tabix_index_filename
from dae.utils.regions import Region

logger = logging.getLogger("annotate_columns")


class ColumnsFormat(AbstractFormat):
    def __init__(
        self,
        pipeline_config: RawPipelineConfig,
        pipeline_config_old: str | None,
        cli_args: dict,
        grr_definition: dict | None,
        region: Region | None,
        input_path: str,
        output_path: str,
        ref_genome_id: str | None,
    ):
        super().__init__(pipeline_config, pipeline_config_old,
                         cli_args, grr_definition, region)
        self.input_path = input_path
        self.output_path = output_path
        self.ref_genome_id = ref_genome_id
        self.input_separator = cli_args["input_separator"]
        self.separator = cli_args["output_separator"]

        self.ref_genome = None
        self.line_iterator = None
        self.header_columns = None
        self.record_to_annotatable = None
        self.annotation_columns = None
        self.output_file = None

    def open(self) -> None:
        super().open()
        assert self.grr is not None
        if self.ref_genome_id:
            res = self.grr.find_resource(self.ref_genome_id)
            if res is not None:
                self.ref_genome = \
                    build_reference_genome_from_resource(res).open()

        _, self.line_iterator, self.header_columns = \
            read_input(self.input_path, self.input_separator, self.region)
        self.record_to_annotatable = build_record_to_annotatable(
            self.cli_args, set(self.header_columns), ref_genome=self.ref_genome)
        self.annotation_columns = [
            attr.name for attr in self.pipeline.get_attributes()  # type: ignore
            if not attr.internal
        ]
        self.output_file = open(self.output_path, "a")  # noqa: SIM115

    def close(self):
        super().close()
        self.output_file.close()  # type: ignore

    def _read(self) -> Generator[dict, None, None]:
        assert self.cli_args is not None
        assert self.header_columns is not None
        assert self.line_iterator is not None

        errors = []
        for lnum, line in enumerate(self.line_iterator):
            try:
                columns = line.strip("\n\r").split(self.input_separator)
                record = dict(zip(self.header_columns, columns, strict=True))
                yield record
            except Exception as ex:  # pylint: disable=broad-except
                logger.exception(
                    "unexpected input data format at line %s: %s",
                    lnum, line)
                errors.append((lnum, line, str(ex)))

        if len(errors) > 0:
            logger.error("there were errors during the import")
            for lnum, line, error in errors:
                logger.error("line %s: %s", lnum, line)
                logger.error("\t%s", error)

    def _apply(self, variant: dict, annotations: list[dict]):
        if isinstance(self.pipeline, ReannotationPipeline):
            for col in self.pipeline.attributes_deleted:  # type: ignore
                del variant[col]

        # No support for multi-allelic variants in columns format
        annotation = annotations[0]

        for col in self.annotation_columns:  # type: ignore
            variant[col] = annotation[col]

    def _convert(self, variant: dict) -> list[tuple[Annotatable, dict]]:
        return [(self.record_to_annotatable.build(variant), dict(variant))]  # type: ignore

    def _write(self, variant: dict) -> None:
        result = self.separator.join(
            stringify(val) for val in variant.values()
        ) + "\n"
        self.output_file.write(result)  # type: ignore


def read_input(
    input_path: str,
    input_separator: str,
    region: Region | None = None,
) -> tuple[Any, Any, list[str]]:
    """Return a file object, line iterator and list of header columns.

    Handles differences between tabixed and non-tabixed input files.
    """
    if input_path.endswith(".gz"):
        tabix_file = TabixFile(input_path)
        with gzip.open(input_path, "rt") as in_file_raw:
            header = in_file_raw.readline() \
                .strip("\r\n") \
                .split(input_separator)
        header = [c.strip("#") for c in header]

        if region is not None:
            iterator = tabix_file.fetch(region.chrom, region.start, region.stop)
        else:
            iterator = tabix_file.fetch()

        return closing(tabix_file), iterator, header
    # pylint: disable=consider-using-with
    text_file = open(input_path, "rt")  # noqa: SIM115
    header = text_file.readline().strip("\r\n").split(input_separator)
    return text_file, text_file, header


def combine(
    args: Any,
    pipeline_config: RawPipelineConfig,
    grr_definition: dict | None,
    partfile_paths: list[str], out_file_path: str,
) -> None:
    """Combine annotated region parts into a single VCF file."""
    grr = build_genomic_resource_repository(definition=grr_definition)
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
        allow_repeated_attributes=args.allow_repeated_attributes,
        work_dir=Path(args.work_dir),
    )
    annotation_attributes = [
        attr.name for attr in pipeline.get_attributes()
        if not attr.internal
    ]

    with gzip.open(args.input, "rt") as in_file_raw:
        header_line = cast(str, in_file_raw.readline())
        hcs = header_line.strip("\r\n").split(args.input_separator)
        header = args.output_separator.join(hcs + annotation_attributes)

    out_file_path = out_file_path.rstrip(".gz")

    with open(out_file_path, "wt") as out_file:
        out_file.write(header + "\n")
        for partfile_path in partfile_paths:
            with open(partfile_path, "rt") as partfile:
                content = partfile.read().strip()
                if content == "":
                    continue
                out_file.write(content)
                out_file.write("\n")

    for partfile_path in partfile_paths:
        os.remove(partfile_path)


class AnnotateColumnsTool(AnnotationTool):
    """Annotation tool for TSV-style text files."""

    def __init__(
        self,
        raw_args: list[str] | None = None,
        gpf_instance: GPFInstance | None = None,
    ) -> None:
        super().__init__(raw_args, gpf_instance)
        self.output = None
        self.ref_genome_id = None

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

        CLIAnnotationContext.add_context_arguments(parser)
        add_record_to_annotable_arguments(parser)
        TaskGraphCli.add_arguments(parser)
        VerbosityConfiguration.set_arguments(parser)
        return parser

    def prepare_for_annotation(self) -> None:
        if self.args.output:
            self.output = self.args.output
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

        pipeline_config_old = None
        if self.args.reannotate:
            pipeline_config_old = Path(self.args.reannotate).read_text()
        pipeline = build_annotation_pipeline(
            self.pipeline.raw, self.grr,
            allow_repeated_attributes=self.args.allow_repeated_attributes,
            work_dir=Path(self.args.work_dir),
            config_old_raw=pipeline_config_old,
            full_reannotation=self.args.full_reannotation,
        )

        _, _, header_columns = \
            read_input(self.args.input, self.args.input_separator)
        annotation_columns = [
            attr.name for attr in pipeline.get_attributes()
            if not attr.internal
        ]
        # WRITE HEADER
        if isinstance(pipeline, ReannotationPipeline):
            old_annotation_columns = {
                attr.name
                for attr in pipeline.pipeline_old.get_attributes()
                if not attr.internal
            }
            new_header = [
                col for col in header_columns
                if col not in old_annotation_columns
            ]
        else:
            new_header = list(header_columns)
        new_header = new_header + annotation_columns
        with open(self.output, "wt") as out_file:
            out_file.write(self.args.output_separator.join(new_header) + "\n")

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
                    [handler, self.args.batch_size > 0],
                    []))

            combine_task = self.task_graph.create_task(
                "combine",
                combine,
                [self.args, self.pipeline.raw, self.grr.definition,
                 file_paths, self.output],
                region_tasks)

            self.task_graph.create_task(
                "compress_and_tabix",
                produce_tabix_index,
                [self.output],
                [combine_task])
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
                [handler, self.args.batch_size > 0],
                [])


def cli(raw_args: list[str] | None = None) -> None:
    tool = AnnotateColumnsTool(raw_args)
    tool.run()


if __name__ == "__main__":
    cli(sys.argv[1:])
