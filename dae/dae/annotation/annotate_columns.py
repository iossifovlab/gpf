from __future__ import annotations

import argparse
import gc
import gzip
import itertools
import logging
import os
import sys
from collections.abc import Iterable, Sequence
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Any, TextIO

from pysam import TabixFile, tabix_compress, tabix_index

from dae.annotation.annotate_utils import (
    add_common_annotation_arguments,
    add_input_files_to_task_graph,
    build_cli_genomic_context,
    cache_pipeline_resources,
    get_grr_from_context,
    get_pipeline_from_context,
    handle_default_args,
    produce_partfile_paths,
    produce_regions,
    stringify,
)
from dae.annotation.annotation_config import (
    AttributeInfo,
    RawAnnotatorsConfig,
    RawPipelineConfig,
)
from dae.annotation.annotation_factory import (
    build_annotation_pipeline,
    load_pipeline_from_file,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    ReannotationPipeline,
)
from dae.annotation.processing_pipeline import (
    Annotation,
    AnnotationPipelineAnnotatablesBatchFilter,
    AnnotationPipelineAnnotatablesFilter,
    AnnotationsWithSource,
    DeleteAttributesFromAWSBatchFilter,
    DeleteAttributesFromAWSFilter,
)
from dae.annotation.record_to_annotatable import (
    RECORD_TO_ANNOTATABLE_CONFIGURATION,
    DaeAlleleRecordToAnnotatable,
    RecordToCNVAllele,
    RecordToPosition,
    RecordToRegion,
    RecordToVcfAllele,
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
from dae.task_graph.graph import TaskGraph, sync_tasks
from dae.utils.fs_utils import tabix_index_filename
from dae.utils.processing_pipeline import Filter, PipelineProcessor, Source
from dae.utils.regions import Region

logger = logging.getLogger("annotate_columns")


class _CSVSource(Source):
    """Source for delimiter-separated values files."""

    def __init__(
        self,
        path: str,
        ref_genome: ReferenceGenome | None,
        columns_args: dict[str, str],
        input_separator: str,
    ):
        self.path = path
        self.ref_genome = ref_genome
        self.columns_args = columns_args
        self.source_file: TextIO | TabixFile
        self.input_separator = input_separator
        self.header: list[str] = self._extract_header()

    def __enter__(self) -> _CSVSource:
        if self.path.endswith(".gz"):
            self.source_file = TabixFile(self.path)
        else:
            self.source_file = open(self.path, "rt")
            self.source_file.readline()  # Skip header line
        if self.ref_genome is not None:
            self.ref_genome.open()
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

        if self.ref_genome is not None:
            self.ref_genome.close()

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
        assert region.start is not None
        return self.source_file.fetch(  # type: ignore
            region.chrom, region.start - 1, region.stop)

    def fetch(
        self, region: Region | None = None,
    ) -> Iterable[AnnotationsWithSource]:
        line_iterator = self._get_line_iterator(region)
        record_to_annotatable = build_record_to_annotatable(
            self.columns_args, set(self.header),
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
            for lnum, line, error in errors:
                logger.error("line %s: %s", lnum, line)
                logger.error("\t%s", error)
            raise ValueError("errors occured during reading of CSV file")


class _CSVBatchSource(Source):
    """Batched source for delimiter-separated values files."""

    def __init__(
        self,
        path: str,
        ref_genome: ReferenceGenome | None,
        columns_args: dict[str, str],
        input_separator: str,
        batch_size: int,
    ):
        self.source = _CSVSource(
            path, ref_genome, columns_args, input_separator)
        self.header = self.source.header
        self.batch_size = batch_size

    def __enter__(self) -> _CSVBatchSource:
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


class _CSVWriter(Filter):
    """Writes delimiter-separated values to a file."""

    def __init__(
        self,
        path: str,
        separator: str,
        header: _CSVHeader,
    ) -> None:
        self.path = path
        self.separator = separator
        self.header = header
        self.out_file: Any

    def __enter__(self) -> _CSVWriter:
        self.out_file = open(self.path, "w")
        header_row = self.separator.join([
            *self.header.input_header,
            *self.header.annotation_header,
        ])
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
        source = data.source
        source_result = {
            col: source[col]
            for col in self.header.input_header
        }
        annotation_result = {
            col: context[col]
            for col in self.header.annotation_header
        }
        self.out_file.write(
            self.separator.join(
                stringify(val)
                for val in [
                    *source_result.values(), *annotation_result.values()]))

        self.out_file.write("\n")


class _CSVBatchWriter(Filter):
    """Writes delimiter-separated values to a file in batches."""

    def __init__(
        self,
        path: str,
        separator: str,
        header: _CSVHeader,
    ) -> None:
        self.writer = _CSVWriter(path, separator, header)

    def __enter__(self) -> _CSVBatchWriter:
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


@dataclass
class _CSVHeader:
    input_header: list[str]
    annotation_header: list[str]


def _build_new_header(
    input_header: list[str],
    annotation_attributes: list[AttributeInfo],
    attributes_to_delete: Sequence[str],
) -> _CSVHeader:
    result = list(input_header)
    for attr_name in attributes_to_delete:
        result.remove(attr_name)
    annotation_header = [
        attr.name for attr in annotation_attributes if not attr.internal
    ]
    return _CSVHeader(
        result,
        annotation_header,
    )


def _build_sequential(
    args: dict[str, Any],
    output_path: str,
    pipeline: AnnotationPipeline,
    reference_genome: ReferenceGenome | None,
    attributes_to_delete: Sequence[str],
) -> PipelineProcessor:
    source = _CSVSource(
        args["input"],
        reference_genome,
        args["columns_args"],
        args["input_separator"],
    )
    filters: list[Filter] = []
    new_header = _build_new_header(
        source.header, pipeline.get_attributes(), attributes_to_delete)
    filters.extend([
        DeleteAttributesFromAWSFilter(attributes_to_delete),
        AnnotationPipelineAnnotatablesFilter(pipeline),
        _CSVWriter(output_path, args["output_separator"], new_header),
    ])
    return PipelineProcessor(source, filters)


def _build_batched(
    args: dict[str, Any],
    output_path: str,
    pipeline: AnnotationPipeline,
    reference_genome: ReferenceGenome | None,
    attributes_to_delete: Sequence[str],
) -> PipelineProcessor:
    source = _CSVBatchSource(
        args["input"],
        reference_genome,
        args["columns_args"],
        args["input_separator"],
        args["batch_size"],
    )
    filters: list[Filter] = []
    new_header = _build_new_header(
        source.header, pipeline.get_attributes(), attributes_to_delete)
    filters.extend([
        DeleteAttributesFromAWSBatchFilter(attributes_to_delete),
        AnnotationPipelineAnnotatablesBatchFilter(pipeline),
        _CSVBatchWriter(output_path, args["output_separator"], new_header),
    ])
    return PipelineProcessor(source, filters)


def _annotate_csv(
    output_path: str,
    pipeline_config: RawAnnotatorsConfig,
    grr_definition: dict,
    reference_genome_resource_id: str | None,
    region: Region | None,
    args: dict[str, Any],
) -> None:
    """Annotate a CSV file using a processing pipeline."""

    build_cli_genomic_context(args)
    grr = build_genomic_resource_repository(definition=grr_definition)

    pipeline_previous = None
    if args["reannotate"]:
        pipeline_previous = load_pipeline_from_file(args["reannotate"], grr)

    ref_genome = None
    if reference_genome_resource_id is not None:
        ref_genome = build_reference_genome_from_resource_id(
            reference_genome_resource_id, grr)

    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
        allow_repeated_attributes=args["allow_repeated_attributes"],
        work_dir=Path(args["work_dir"]),
    )

    attributes_to_delete = []

    if pipeline_previous:
        pipeline = ReannotationPipeline(
            pipeline, pipeline_previous,
            full_reannotation=args["full_reannotation"])
        attributes_to_delete = pipeline.deleted_attributes

    build_processor = _build_sequential \
        if args["batch_size"] <= 0 \
        else _build_batched

    processor = build_processor(
        args,
        output_path,
        pipeline,
        ref_genome,
        attributes_to_delete,
    )

    with processor:
        processor.process_region(region)


def _concat(
    partfile_paths: list[str],
    output_path: str,
    keep_parts: bool,  # noqa: FBT001
) -> None:
    """Concatenate multiple CSV files into a single CSV file *in order*."""
    # Get any header from the partfiles, they should all be equal
    # and usable as a final output header
    with open(partfile_paths[0], "r") as partfile:
        header = partfile.readline().strip()

    with open(output_path, "w") as outfile:
        outfile.write(header)

        for path in partfile_paths:
            with open(path, "r") as partfile:
                partfile.readline()  # skip header
                for line in partfile:
                    outfile.write("\n")
                    outfile.write(line.strip("\r\n"))

        outfile.write("\n")

    if not keep_parts:
        for partfile_path in partfile_paths:
            os.remove(partfile_path)


def _read_header(filepath: str, separator: str = "\t") -> list[str]:
    """Extract header from columns file."""
    if filepath.endswith(".gz"):
        file = gzip.open(filepath, "rt")  # noqa: SIM115
    else:
        file = open(filepath, "r")  # noqa: SIM115
    with file:
        header = file.readline()
    return [c.strip() for c in header.split(separator)]


def _tabix_compress(filepath: str) -> None:
    tabix_compress(filepath, f"{filepath}.gz", force=True)


def _tabix_index(filepath: str, args: dict | None = None) -> None:
    """Produce a tabix index file for the given variants file."""
    header = _read_header(filepath)
    line_skip = 0 if header[0].startswith("#") else 1
    header = [c.strip("#") for c in header]
    record_to_annotatable = build_record_to_annotatable(
        args if args is not None else {},
        set(header),
    )
    if isinstance(record_to_annotatable, (RecordToRegion,
                                          RecordToCNVAllele)):
        seq_col = header.index(record_to_annotatable.chrom_col)
        start_col = header.index(record_to_annotatable.pos_beg_col)
        end_col = header.index(record_to_annotatable.pos_end_col)
    elif isinstance(record_to_annotatable, RecordToVcfAllele):
        seq_col = header.index(record_to_annotatable.chrom_col)
        start_col = header.index(record_to_annotatable.pos_col)
        end_col = start_col
    elif isinstance(
            record_to_annotatable,
            (RecordToPosition, DaeAlleleRecordToAnnotatable)):
        seq_col = header.index(record_to_annotatable.chrom_column)
        start_col = header.index(record_to_annotatable.pos_column)
        end_col = start_col
    else:
        raise TypeError(
            "Could not generate tabix index: record"
            f" {type(record_to_annotatable)} is of unsupported type.")
    logger.info(
        "producing tabix index for '%s': "
        "tabix_index(%s, seq_col=%s, start_col=%s, end_col=%s, "
        "line_skip=%s, force=True)",
        filepath, filepath, seq_col, start_col, end_col, line_skip)
    try:
        tabix_index(filepath,
                    seq_col=seq_col,
                    start_col=start_col,
                    end_col=end_col,
                    line_skip=line_skip,
                    force=True)
    except Exception:  # pylint: disable=broad-except
        logger.exception("failed to create tabix index for '%s'", filepath)
        raise


def _add_tasks_tabixed(
    args: dict[str, Any],
    task_graph: TaskGraph,
    output_path: str,
    pipeline_config: RawPipelineConfig,
    grr_definition: dict[str, Any],
    ref_genome_id: str | None,
) -> None:
    with closing(TabixFile(args["input"])) as pysam_file:
        regions = produce_regions(pysam_file, args["region_size"])
    file_paths = produce_partfile_paths(
        args["input"], regions, args["work_dir"])

    annotation_tasks = []
    for region, path in zip(regions, file_paths, strict=True):
        annotation_tasks.append(task_graph.create_task(
            f"part-{str(region).replace(':', '-')}",
            _annotate_csv,
            args=[
                path,
                pipeline_config,
                grr_definition,
                ref_genome_id,
                region,
                args,
            ],
            deps=[]))

    annotation_sync = task_graph.create_task(
        "sync_csv_write",
        sync_tasks,
        args=[],
        deps=annotation_tasks,
    )

    concat_task = task_graph.create_task(
        "concat",
        _concat,
        args=[file_paths, output_path, args["keep_parts"]],
        deps=[annotation_sync])

    compress_task = task_graph.create_task(
        "tabix_compress",
        _tabix_compress,
        args=[output_path],
        deps=[concat_task])

    task_graph.create_task(
        "tabix_index",
        _tabix_index,
        args=[f"{output_path}.gz", args["columns_args"]],
        deps=[compress_task])


def _add_tasks_plaintext(
    args: dict[str, Any],
    task_graph: TaskGraph,
    output_path: str,
    pipeline_config: RawPipelineConfig,
    grr_definition: dict[str, Any],
    ref_genome_id: str | None,
) -> None:
    task_graph.create_task(
        "annotate_all",
        _annotate_csv,
        args=[
            output_path,
            pipeline_config,
            grr_definition,
            ref_genome_id,
            None,
            args,
        ],
        deps=[])


def _build_argument_parser() -> argparse.ArgumentParser:
    """Configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Annotate columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_record_to_annotable_arguments(parser)
    parser.add_argument(
        "--input-separator", "--in-sep", default="\t",
        help="The column separator in the input")
    parser.add_argument(
        "--output-separator", "--out-sep", default=None,
        help="The column separator in the output")

    add_common_annotation_arguments(parser)

    return parser


def _adjust_default_output_separator(args: dict[str, Any]) -> dict[str, Any]:
    if args["output_separator"] is None:
        args["output_separator"] = args["input_separator"]
    return args


def cli(argv: list[str] | None = None) -> None:
    """Entry point for running the columns annotation tool."""
    if not argv:
        argv = sys.argv[1:]

    arg_parser = _build_argument_parser()
    args = vars(arg_parser.parse_args(argv))

    VerbosityConfiguration.set_verbosity(args["verbose"])
    args = handle_default_args(args)
    args = _adjust_default_output_separator(args)

    context = build_cli_genomic_context(args)
    pipeline = get_pipeline_from_context(context)
    grr = get_grr_from_context(context)
    assert grr.definition is not None

    ref_genome = context.get_reference_genome()
    ref_genome_id = ref_genome.resource_id if ref_genome else None

    cache_pipeline_resources(grr, pipeline)

    args["columns_args"] = {
        f"col_{col}": args[f"col_{col}"]
        for cols in RECORD_TO_ANNOTATABLE_CONFIGURATION
        for col in cols
    }

    output_path = args["output"]

    task_graph = TaskGraph()
    if tabix_index_filename(args["input"]):
        _add_tasks_tabixed(
            args,
            task_graph,
            output_path,
            pipeline.raw,
            grr.definition,
            ref_genome_id,
        )
    else:
        _add_tasks_plaintext(
            args,
            task_graph,
            output_path,
            pipeline.raw,
            grr.definition,
            ref_genome_id,
        )

    add_input_files_to_task_graph(args, task_graph)
    TaskGraphCli.process_graph(task_graph, **args)

    pipeline.close()
    if ref_genome is not None:
        ref_genome.close()

    gc.collect()
