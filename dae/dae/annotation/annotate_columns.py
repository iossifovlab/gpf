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
    AnnotationTool,
    produce_partfile_paths,
    produce_regions,
    produce_tabix_index,
    stringify,
)
from dae.annotation.annotation_config import (
    RawAnnotatorsConfig,
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

    @staticmethod
    def _read(
        input_path: str,
        input_separator: str,
        region: Region | None,
        grr_definition: dict | None,
        ref_genome_id: str | None,
        kwargs: dict,
    ) -> Generator[tuple[dict, Annotatable], None, None]:
        _, line_iterator, header_columns = \
            read_input(input_path, input_separator, region)

        grr = build_genomic_resource_repository(definition=grr_definition)
        ref_genome = None
        if ref_genome_id:
            res = grr.find_resource(ref_genome_id)
            if res is not None:
                ref_genome = build_reference_genome_from_resource(res).open()

        errors = []
        record_to_annotatable = build_record_to_annotatable(
            kwargs, set(header_columns), ref_genome=ref_genome)
        for lnum, line in enumerate(line_iterator):
            try:
                columns = line.strip("\n\r").split(input_separator)
                record = dict(zip(header_columns, columns, strict=True))
                yield record, record_to_annotatable.build(record)
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

    @staticmethod
    def _write(
        data: Generator[tuple[dict, dict], None, None],
        annotation_columns: list[str],
        out_file_path: str,
        separator: str,
    ) -> None:
        with open(out_file_path, "a") as out_file:
            for record, annotation in data:
                for col in annotation_columns:
                    record[col] = annotation[col]
                result = separator.join(
                    stringify(val) for val in record.values()
                ) + "\n"
                out_file.write(result)

    @classmethod
    def annotate(
        cls,
        args: argparse.Namespace,
        pipeline_config: RawAnnotatorsConfig,
        grr_definition: dict | None,
        ref_genome_id: str | None,
        out_file_path: str,
        region: Region | None = None,
    ) -> None:
        """Annotate a variants file with a given pipeline configuration."""
        # Insisting on having the pipeline config passed in args
        # prevents the finding of a default annotation config. Consider fixing
        pipeline_config_old = None
        if args.reannotate:
            pipeline_config_old = Path(args.reannotate).read_text()
        grr_definition_copy = dict(grr_definition) \
            if grr_definition is not None else None
        grr = build_genomic_resource_repository(definition=grr_definition)
        pipeline = build_annotation_pipeline(
            pipeline_config, grr,
            allow_repeated_attributes=args.allow_repeated_attributes,
            work_dir=Path(args.work_dir),
            config_old_raw=pipeline_config_old,
            full_reannotation=args.full_reannotation,
        )
        annotation_columns = [
            attr.name for attr in pipeline.get_attributes()
            if not attr.internal
        ]

        data = cls._read(
            args.input,
            args.input_separator,
            region,
            grr_definition_copy,
            ref_genome_id,
            vars(args),
        )

        pipeline.open()
        if args.batch_size > 0:
            annotated_data = cls.annotate_batched(
                data,
                pipeline,
                args.batch_size,
                cls.get_task_dir(region),
            )
        else:
            annotated_data = cls.annotate_iterative(
                data,
                pipeline,
            )
        pipeline.close()

        cls._write(
            annotated_data,
            annotation_columns,
            out_file_path,
            args.output_separator,
        )

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
        if tabix_index_filename(self.args.input):
            with closing(TabixFile(self.args.input)) as pysam_file:
                regions = produce_regions(pysam_file, self.args.region_size)
            file_paths = produce_partfile_paths(
                self.args.input, regions, self.args.work_dir)

            region_tasks = []
            for region, path in zip(regions, file_paths, strict=True):
                task_id = f"part-{str(region).replace(':', '-')}"
                region_tasks.append(self.task_graph.create_task(
                    task_id,
                    AnnotateColumnsTool.annotate,
                    [self.args, self.pipeline.raw,
                     self.grr.definition,
                     self.ref_genome_id, path, region],
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
            self.task_graph.create_task(
                "annotate_all",
                AnnotateColumnsTool.annotate,
                [self.args, self.pipeline.raw, self.grr.definition,
                 self.ref_genome_id, self.output, None],
                [])


def cli(raw_args: list[str] | None = None) -> None:
    tool = AnnotateColumnsTool(raw_args)
    tool.run()


if __name__ == "__main__":
    cli(sys.argv[1:])
