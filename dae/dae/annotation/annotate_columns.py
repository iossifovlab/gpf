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
from typing import Any, TextIO

from pysam import TabixFile

from dae.annotation.annotate_utils import (
    add_input_files_to_task_graph,
    get_stuff_from_context,
    produce_partfile_paths,
    produce_regions,
    produce_tabix_index,
    setup_context,
    setup_work_dir_and_task_dirs,
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
from dae.annotation.genomic_context import CLIAnnotationContextProvider
from dae.annotation.processing_pipeline import (
    Annotation,
    AnnotationPipelineAnnotatablesBatchFilter,
    AnnotationPipelineAnnotatablesFilter,
    AnnotationsWithSource,
    DeleteAttributesFromAWSBatchFilter,
    DeleteAttributesFromAWSFilter,
)
from dae.annotation.record_to_annotatable import (
    add_record_to_annotable_arguments,
    build_record_to_annotatable,
)
from dae.genomic_resources.cached_repository import cache_resources
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource_id,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph
from dae.utils.fs_utils import tabix_index_filename
from dae.utils.processing_pipeline import Filter, PipelineProcessor, Source
from dae.utils.regions import Region

logger = logging.getLogger("annotate_columns")


class CSVSource(Source):
    """Source for delimiter-separated values files."""

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
        self.source_file: TextIO | TabixFile
        self.input_separator = input_separator
        self.header: list[str] = self._extract_header()

    def __enter__(self) -> CSVSource:
        if self.path.endswith(".gz"):
            self.source_file = TabixFile(self.path)
        else:
            self.source_file = open(self.path, "rt")
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

        return exc_type is None

    def _extract_header(self) -> list[str]:
        if self.path.endswith(".gz"):
            with gzip.open(self.path, "rt") as in_file_raw:
                raw_header = in_file_raw.readline()
        else:
            with open(self.path, "rt") as in_file_raw:
                raw_header = in_file_raw.readline()

        return [
            c.strip("#")
            for c in raw_header.strip("\r\n").split(self.input_separator)
        ]

    def _get_line_iterator(self, region: Region | None) -> Iterable:
        if not isinstance(self.source_file, TabixFile):
            return self.source_file
        if region is None:
            return self.source_file.fetch()  # type: ignore
        return self.source_file.fetch(  # type: ignore
            region.chrom, region.start, region.stop)

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


class CSVBatchSource(Source):
    """Batched source for delimiter-separated values files."""

    def __init__(
        self,
        path: str,
        ref_genome: ReferenceGenome,
        cli_args: Any,
        input_separator: str,
        batch_size: int = 500,
    ):
        self.source = CSVSource(path, ref_genome, cli_args, input_separator)
        self.header = self.source.header
        self.batch_size = batch_size

    def __enter__(self) -> CSVBatchSource:
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

        return exc_type is None

    def fetch(
        self, region: Region | None = None,
    ) -> Iterable[Sequence[AnnotationsWithSource]]:
        records = self.source.fetch(region)
        while batch := tuple(itertools.islice(records, self.batch_size)):
            yield batch


class CSVWriter(Filter):
    """Writes delimiter-separated values to a file."""

    def __init__(
        self,
        path: str,
        separator: str,
        header: list[str],
    ) -> None:
        self.path = path
        self.separator = separator
        self.header = header
        self.out_file: Any

    def __enter__(self) -> CSVWriter:
        self.out_file = open(self.path, "w")
        header_row = self.separator.join(self.header)
        self.out_file.write(f"{header_row}\n")
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

        return exc_type is None

    def filter(self, data: AnnotationsWithSource) -> None:
        context = data.annotations[0].context
        result = {
            col: context[col] if col in context else data.source[col]
            for col in self.header
        }
        self.out_file.write(
            self.separator.join(stringify(val) for val in result.values())
            + "\n",
        )


class CSVBatchWriter(Filter):
    """Writes delimiter-separated values to a file in batches."""

    def __init__(
        self,
        path: str,
        separator: str,
        header: list[str],
    ) -> None:
        self.writer = CSVWriter(path, separator, header)

    def __enter__(self) -> CSVBatchWriter:
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

        return exc_type is None

    def filter(self, data: Sequence[AnnotationsWithSource]) -> None:
        for record in data:
            self.writer.filter(record)


def process_dsv(  # pylint: disable=too-many-positional-arguments
    input_path: str,
    output_path: str,
    pipeline_config: RawAnnotatorsConfig,
    pipeline_config_old: str | None,
    grr_definition: dict,
    reference_genome_resource_id: str,
    work_dir: Path,
    batch_size: int,
    region: Region | None,
    cli_args: dict[str, Any],
    input_separator: str,
    output_separator: str,
    allow_repeated_attributes: bool,  # noqa: FBT001
    full_reannotation: bool,  # noqa: FBT001
) -> None:
    """Annotate a CSV file using a processing pipeline."""
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

    if batch_size <= 0:
        source = CSVSource(
            input_path, reference_genome, cli_args, input_separator)
        new_header = list(source.header)
        if isinstance(pipeline, ReannotationPipeline):
            filters.append(DeleteAttributesFromAWSFilter(
                pipeline.attributes_deleted))
            for attr in pipeline.pipeline_old.get_attributes():
                if not attr.internal:
                    new_header.remove(attr.name)
        new_header = new_header + [
            attr.name for attr in pipeline.get_attributes()
            if not attr.internal
        ]
        filters.extend([
            AnnotationPipelineAnnotatablesFilter(pipeline),
            CSVWriter(output_path, output_separator, new_header),
        ])
    else:
        source = CSVBatchSource(
            input_path, reference_genome, cli_args, input_separator)
        new_header = list(source.header)
        if isinstance(pipeline, ReannotationPipeline):
            filters.append(DeleteAttributesFromAWSBatchFilter(
                pipeline.attributes_deleted))
            for attr in pipeline.pipeline_old.get_attributes():
                if not attr.internal:
                    new_header.remove(attr.name)
        new_header = new_header + [
            attr.name for attr in pipeline.get_attributes()
            if not attr.internal
        ]
        filters.extend([
            AnnotationPipelineAnnotatablesBatchFilter(pipeline),
            CSVBatchWriter(output_path, output_separator, new_header),
        ])

    with PipelineProcessor(source, filters) as processor:
        processor.process_region(region)


def concat(partfile_paths: list[str], output_path: str) -> None:
    """Concatenate multiple CSV files into a single CSV file *in order*."""
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


class AnnotateColumnsTool:
    """Annotation tool for TSV-style text files."""

    def __init__(self, args: dict[str, Any]) -> None:
        self.args = args

    @staticmethod
    def get_argument_parser() -> argparse.ArgumentParser:
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

    @staticmethod
    def get_output_path(args: dict[str, Any]) -> str:
        if args["output"]:
            return args["output"].rstrip(".gz")

        input_name = args["input"].rstrip(".gz")
        if "." in input_name:
            idx = input_name.find(".")
            return f"{input_name[:idx]}_annotated{input_name[idx:]}"

        return f"{input_name}_annotated"

    def add_tasks(
        self,
        task_graph: TaskGraph,
        pipeline_config: RawPipelineConfig,
        grr_definition: dict[str, Any],
        ref_genome_id: str,
    ) -> None:
        self.output: str = AnnotateColumnsTool.get_output_path(self.args)

        pipeline_config_old = None
        if self.args["reannotate"]:
            pipeline_config_old = Path(self.args["reannotate"]).read_text()

        if tabix_index_filename(self.args["input"]):
            with closing(TabixFile(self.args["input"])) as pysam_file:
                regions = produce_regions(pysam_file, self.args["region_size"])
            file_paths = produce_partfile_paths(
                self.args["input"], regions, self.args["work_dir"])

            annotation_tasks = []
            for region, path in zip(regions, file_paths, strict=True):
                task_id = f"part-{str(region).replace(':', '-')}"

                annotation_tasks.append(task_graph.create_task(
                    task_id,
                    process_dsv,
                    args=[
                        self.args["input"],
                        path,
                        pipeline_config,
                        pipeline_config_old,
                        grr_definition,
                        ref_genome_id,
                        Path(self.args["work_dir"]),
                        self.args["batch_size"],
                        region,
                        self.args,
                        self.args["input_separator"],
                        self.args["output_separator"],
                        self.args["allow_repeated_attributes"],
                        self.args["full_reannotation"],
                    ],
                    deps=[]))

            annotation_sync = task_graph.create_task(
                "sync_dsv_write", lambda: None,
                args=[], deps=annotation_tasks,
            )

            concat_task = task_graph.create_task(
                "concat",
                concat,
                args=[
                    file_paths,
                    self.output,
                ],
                deps=[annotation_sync])

            task_graph.create_task(
                "compress_and_tabix",
                produce_tabix_index,
                args=[self.output, self.args],
                deps=[concat_task])
        else:
            task_graph.create_task(
                "annotate_all",
                process_dsv,
                args=[
                    self.args["input"],
                    self.output,
                    pipeline_config,
                    pipeline_config_old,
                    grr_definition,
                    ref_genome_id,
                    Path(self.args["work_dir"]),
                    self.args["batch_size"],
                    None,
                    self.args,
                    self.args["input_separator"],
                    self.args["output_separator"],
                    self.args["allow_repeated_attributes"],
                    self.args["full_reannotation"],
                ],
                deps=[])


def cli(raw_args: list[str] | None = None) -> None:
    if not raw_args:
        raw_args = sys.argv[1:]

    arg_parser = AnnotateColumnsTool.get_argument_parser()
    args = vars(arg_parser.parse_args(raw_args))

    setup_context(args)

    pipeline, context, grr = get_stuff_from_context()
    assert grr.definition is not None

    resource_ids: set[str] = {
        res.resource_id
        for annotator in pipeline.annotators
        for res in annotator.resources
    }
    cache_resources(grr, resource_ids)

    ref_genome = context.get_reference_genome()
    assert ref_genome is not None

    ref_genome_id = ref_genome.resource_id

    tool = AnnotateColumnsTool(args)

    task_graph = TaskGraph()

    setup_work_dir_and_task_dirs(tool.args)

    tool.add_tasks(
        task_graph,
        pipeline.raw,
        grr.definition,
        ref_genome_id,
    )

    if len(task_graph.tasks) > 0:
        add_input_files_to_task_graph(tool.args, task_graph)
        TaskGraphCli.process_graph(task_graph, **tool.args)
