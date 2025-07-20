from __future__ import annotations

import argparse
import gzip
import itertools
import logging
import os
import sys
from collections.abc import Iterable, Sequence
from contextlib import closing
from pathlib import Path
from types import TracebackType
from typing import Any

from pysam import TabixFile

from dae.annotation.annotate_utils import (
    AnnotationTool,
    produce_partfile_paths,
    produce_regions,
    produce_tabix_index,
)
from dae.annotation.annotation_config import (
    RawAnnotatorsConfig,
)
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import (
    ReannotationPipeline,
)
from dae.annotation.format_handlers import stringify
from dae.annotation.genomic_context import CLIAnnotationContextProvider
from dae.annotation.processing_pipeline import (
    Annotation,
    AnnotationPipelineAnnotatablesBatchFilter,
    AnnotationPipelineAnnotatablesFilter,
    AnnotationsWithSource,
)
from dae.annotation.record_to_annotatable import (
    add_record_to_annotable_arguments,
    build_record_to_annotatable,
)
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource_id,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.task_graph import TaskGraphCli
from dae.utils.fs_utils import tabix_index_filename
from dae.utils.processing_pipeline import Filter, PipelineProcessor, Source
from dae.utils.regions import Region

logger = logging.getLogger("annotate_columns")


class DSVSource(Source):
    def __init__(
        self,
        path: str,
        ref_genome: ReferenceGenome,
        cli_args: Any,
        input_separator: str,
    ):
        self.path = path
        self.ref_genome = ref_genome
        self.cli_args = cli_args
        self.source_file: Any
        self.header: list[str] = []
        self.input_separator = input_separator

    def __enter__(self) -> DSVSource:
        if self.path.endswith(".gz"):
            self.source_file = TabixFile(self.path)
            with gzip.open(self.path, "rt") as in_file_raw:
                raw_header = in_file_raw.readline()
        else:
            self.source_file = open(self.path, "rt")
            raw_header = self.source_file.readline()

        # Set header columns
        self.header = [
            c.strip("#")
            for c in raw_header.strip("\r\n").split(self.input_separator)
        ]

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.source_file.close()

        return exc_type is not None

    def _get_line_iterator(self, region: Region | None) -> Iterable:
        if not self.path.endswith(".gz"):
            return self.source_file
        if region is None:
            return self.source_file.fetch()
        return self.source_file.fetch(region.chrom, region.start, region.stop)

    def fetch(
        self, region: Region | None = None,
    ) -> Iterable[AnnotationsWithSource]:
        line_iterator = self._get_line_iterator(region)
        record_to_annotatable = build_record_to_annotatable(
            self.cli_args, set(self.header),
            ref_genome=self.ref_genome)
        errors = []

        for lnum, line in enumerate(line_iterator):
            try:
                columns = line.strip("\n\r").split(self.input_separator)
                record = dict(zip(self.header, columns, strict=True))
                annotatable = record_to_annotatable.build(record)
                yield AnnotationsWithSource(
                    record, [Annotation(annotatable, dict(record))],
                )
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


class DSVBatchSource(Source):
    def __init__(
        self,
        path: str,
        ref_genome: ReferenceGenome,
        cli_args: Any,
        input_separator: str,
        batch_size: int = 500,
    ):
        self.source = DSVSource(path, ref_genome, cli_args, input_separator)
        self.batch_size = batch_size

    def __enter__(self) -> DSVBatchSource:
        self.source.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.source.__exit__(exc_type, exc_value, exc_tb)

        return exc_type is not None

    def fetch(
        self, region: Region | None = None,
    ) -> Iterable[Sequence[AnnotationsWithSource]]:
        records = self.source.fetch(region)
        while batch := tuple(itertools.islice(records, self.batch_size)):
            yield batch


class DSVWriter(Filter):
    def __init__(
        self,
        path: str,
        separator: str,
        ignored_cols: set[str],
    ) -> None:
        self.path = path
        self.separator = separator
        self.header_written = False
        self.out_file: Any
        self.ignored_cols = ignored_cols

    def __enter__(self) -> DSVWriter:
        self.out_file = open(self.path, "w")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.out_file.close()

        return exc_type is not None

    def _write_header(self, record: dict) -> None:
        header = self.separator.join([col for col in record
                                      if col not in self.ignored_cols])
        self.out_file.write(f"{header}\n")
        self.header_written = True

    def filter(self, data: AnnotationsWithSource) -> None:
        result = dict(data.source)
        for col, val in data.annotations[0].context.items():
            if col in self.ignored_cols:
                continue
            result[col] = val

        if not self.header_written:
            self._write_header(result)

        self.out_file.write(
            self.separator.join(stringify(val) for val in result.values())
            + "\n",
        )  # type: ignore


class DSVBatchWriter(Filter):
    def __init__(
        self,
        path: str,
        separator: str,
        ignored_cols: set[str],
    ) -> None:
        self.writer = DSVWriter(path, separator, ignored_cols)

    def __enter__(self) -> DSVBatchWriter:
        self.writer.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.writer.__exit__(exc_type, exc_value, exc_tb)

        return exc_type is not None

    def filter(self, data: Sequence[AnnotationsWithSource]) -> None:
        for record in data:
            self.writer.filter(record)


class DeleteAttributesFromAWSFilter(Filter):
    """Filter to remove items from AWSs. Works in-place."""

    def __init__(self, attributes_to_remove: Sequence[str]) -> None:
        self.to_remove = set(attributes_to_remove)

    def filter(self, data: AnnotationsWithSource) -> AnnotationsWithSource:
        for attr in self.to_remove:
            del data.source[attr]
        return data


class DeleteAttributesFromAWSBatchFilter(Filter):
    """Filter to remove items from AWS batches. Works in-place."""

    def __init__(self, attributes_to_remove: Sequence[str]) -> None:
        self._delete_filter = DeleteAttributesFromAWSFilter(
            attributes_to_remove)

    def filter(
        self, data: Sequence[AnnotationsWithSource],
    ) -> Sequence[AnnotationsWithSource]:
        for aws in data:
            self._delete_filter.filter(aws)
        return data


def process_dsv(
    input_path: str,
    output_path: str,
    pipeline_config: RawAnnotatorsConfig,
    pipeline_config_old: str | None,
    grr_definition: dict,
    reference_genome_resource_id: str,
    work_dir: Path,
    batch_size: int,
    region: Region | None,
    cli_args: Any,
    input_separator: str,
    output_separator: str,
    allow_repeated_attributes: bool,  # noqa: FBT001
    full_reannotation: bool,  # noqa: FBT001
) -> None:
    """Annotate a DSV file using a processing pipeline."""
    grr = build_genomic_resource_repository(definition=grr_definition)
    reference_genome = build_reference_genome_from_resource_id(
        reference_genome_resource_id, grr)
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
        allow_repeated_attributes=allow_repeated_attributes,
        work_dir=work_dir,
        config_old_raw=pipeline_config_old,
        full_reannotation=full_reannotation,
    )

    source: Source
    filters: list[Filter] = []

    internal_cols = {
        attr.name for attr in pipeline.get_attributes()
        if attr.internal
    }

    if batch_size <= 0:
        source = DSVSource(
            input_path, reference_genome, cli_args, input_separator)
        if isinstance(pipeline, ReannotationPipeline):
            filters.append(DeleteAttributesFromAWSFilter(
                pipeline.attributes_deleted))
        filters.extend([
            AnnotationPipelineAnnotatablesFilter(pipeline),
            DSVWriter(output_path, output_separator, internal_cols),
        ])
    else:
        source = DSVBatchSource(
            input_path, reference_genome, cli_args, input_separator)
        if isinstance(pipeline, ReannotationPipeline):
            filters.append(DeleteAttributesFromAWSBatchFilter(
                pipeline.attributes_deleted))
        filters.extend([
            AnnotationPipelineAnnotatablesBatchFilter(pipeline),
            DSVBatchWriter(output_path, output_separator, internal_cols),
        ])

    with PipelineProcessor(source, filters) as processor:
        processor.process_region(region)


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

            annotation_tasks = []
            for region, path in zip(regions, file_paths, strict=True):
                task_id = f"part-{str(region).replace(':', '-')}"

                annotation_tasks.append(self.task_graph.create_task(
                    task_id,
                    process_dsv,
                    args=[
                        self.args.input,
                        path,
                        self.pipeline.raw,
                        pipeline_config_old,
                        self.grr.definition,
                        self.ref_genome_id,
                        Path(self.args.work_dir),
                        self.args.batch_size,
                        region,
                        vars(self.args),
                        self.args.input_separator,
                        self.args.output_separator,
                        self.args.allow_repeated_attributes,
                        self.args.full_reannotation,
                    ],
                    deps=[]))

            annotation_sync = self.task_graph.create_task(
                "sync_dsv_write", lambda: None,
                args=[], deps=annotation_tasks,
            )

            concat_task = self.task_graph.create_task(
                "concat",
                concat,
                args=[
                    file_paths,
                    self.output,
                ],
                deps=[annotation_sync])

            self.task_graph.create_task(
                "compress_and_tabix",
                produce_tabix_index,
                args=[self.output, self.args],
                deps=[concat_task])
        else:
            self.task_graph.create_task(
                "annotate_all",
                process_dsv,
                args=[
                    self.args.input,
                    self.output,
                    self.pipeline.raw,
                    pipeline_config_old,
                    self.grr.definition,
                    self.ref_genome_id,
                    Path(self.args.work_dir),
                    self.args.batch_size,
                    None,
                    vars(self.args),
                    self.args.input_separator,
                    self.args.output_separator,
                    self.args.allow_repeated_attributes,
                    self.args.full_reannotation,
                ],
                deps=[])


def cli(raw_args: list[str] | None = None) -> None:
    tool = AnnotateColumnsTool(raw_args)
    tool.run()


if __name__ == "__main__":
    cli(sys.argv[1:])
