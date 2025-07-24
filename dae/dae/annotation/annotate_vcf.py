from __future__ import annotations

import argparse
import itertools
import logging
import os
import sys
from collections.abc import Iterable, Sequence
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Any

from pysam import (
    TabixFile,
    VariantFile,
    VariantHeader,
    VariantRecord,
    tabix_index,
)

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotate_utils import (
    add_input_files_to_task_graph,
    build_output_path,
    cache_pipeline_resources,
    get_stuff_from_context,
    produce_partfile_paths,
    produce_regions,
    stringify,
)
from dae.annotation.annotation_config import (
    AttributeInfo,
    RawAnnotatorsConfig,
    RawPipelineConfig,
)
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    ReannotationPipeline,
)
from dae.annotation.genomic_context import CLIAnnotationContextProvider
from dae.annotation.processing_pipeline import (
    Annotation,
    AnnotationPipelineAnnotatablesBatchFilter,
    AnnotationPipelineAnnotatablesFilter,
    AnnotationsWithSource,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph
from dae.utils.fs_utils import tabix_index_filename
from dae.utils.processing_pipeline import Filter, PipelineProcessor, Source
from dae.utils.regions import Region
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("annotate_vcf")


@dataclass
class _ProcessingArgs:
    input: str
    reannotate: str | None
    work_dir: str
    batch_size: int
    region_size: int
    allow_repeated_attributes: bool
    full_reannotation: bool


class _VCFSource(Source):
    """Source for reading from VCF files."""

    def __init__(self, path: str):
        self.path = path
        self.vcf: VariantFile
        with VariantFile(self.path, "r") as infile:
            self.header = infile.header

    def __enter__(self) -> _VCFSource:
        self.vcf = VariantFile(self.path, "r")
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

        self.vcf.close()

        return exc_type is None

    @staticmethod
    def _convert(variant: VariantRecord) -> AnnotationsWithSource:
        annotations = [
            Annotation(
                VCFAllele(variant.chrom,
                          variant.pos,
                          variant.ref,  # type: ignore
                          alt),
                {k: v[idx] for k, v in variant.info.items()},
            )
            for idx, alt in enumerate(variant.alts)  # type: ignore
        ]
        return AnnotationsWithSource(variant, annotations)

    def fetch(
        self, region: Region | None = None,
    ) -> Iterable[AnnotationsWithSource]:
        if region is None:
            in_file_iter = self.vcf.fetch()
        else:
            in_file_iter = self.vcf.fetch(region.chrom,
                                          region.start,
                                          region.stop)

        for vcf_var in in_file_iter:
            if vcf_var.ref is None:
                logger.warning(
                    "vcf variant without reference: %s %s",
                    vcf_var.chrom, vcf_var.pos,
                )
                continue

            if vcf_var.alts is None:
                logger.info(
                    "vcf variant without alternatives: %s %s",
                    vcf_var.chrom, vcf_var.pos,
                )
                continue

            yield _VCFSource._convert(vcf_var)


class _VCFBatchSource(Source):
    """Source for reading from VCF files in batches."""

    def __init__(
        self,
        path: str,
        batch_size: int = 500,
    ):
        self.source = _VCFSource(path)
        self.batch_size = batch_size

    def __enter__(self) -> _VCFBatchSource:
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


class _VCFWriter(Filter):
    """A filter that writes variants to a VCF file."""

    def __init__(
        self,
        path: str,
        pipeline: AnnotationPipeline,
        header: VariantHeader,
    ):
        self.path = path
        self.pipeline = pipeline
        self.header = self._update_header(header, pipeline)
        self.output_file: VariantFile
        self.annotation_attributes = self.pipeline.get_attributes()

    @staticmethod
    def _update_header(
        header: VariantHeader,
        pipeline: AnnotationPipeline,
    ) -> VariantHeader:
        """Update a variant file's header with annotation pipeline scores."""
        assert pipeline is not None

        header.add_meta("pipeline_annotation_tool", "GPF variant annotation.")
        if isinstance(pipeline, ReannotationPipeline):
            header_info_keys = header.info.keys()
            old_annotation_columns = {
                attr.name
                for attr in pipeline.pipeline_old.get_attributes()
                if not attr.internal
            }
            new_annotation_columns = {
                attr.name for attr in pipeline.get_attributes()
                if not attr.internal
            }

            for info_key in header_info_keys:
                if (info_key in old_annotation_columns
                   and info_key not in new_annotation_columns):
                    header.info.remove_header(info_key)

            attributes = []
            for attr in pipeline.get_attributes():
                if attr.internal:
                    continue

                if attr.name not in header.info:
                    attributes.append(attr)
        else:
            attributes = pipeline.get_attributes()

        for attribute in attributes:
            description = attribute.description
            description = description.replace("\n", " ")
            description = description.replace('"', '\\"')
            header.info.add(attribute.name, "A", "String", description)
        return header

    @staticmethod
    def _convert_to_string(buff: list[Any]) -> list[str]:
        result = []
        for attr in buff:
            if isinstance(attr, list):
                attr = ";".join(stringify(a, vcf=True) for a in attr)
            elif isinstance(attr, dict):
                attr = ";".join(
                    f"{k}:{v}"
                    for k, v in attr.items()
                )
            result.append(stringify(attr, vcf=True)
                .replace(";", "|")
                .replace(",", "|")
                .replace(" ", "_"))
        return result

    @staticmethod
    def _update_variant(
        vcf_var: VariantRecord,
        allele_annotations: list[dict],
        attributes: list[AttributeInfo],
        pipeline: AnnotationPipeline,
    ) -> None:
        buffers: list[list] = [[] for _ in attributes]
        for annotation in allele_annotations:
            if isinstance(pipeline, ReannotationPipeline):
                for col in pipeline.attributes_deleted:
                    del vcf_var.info[col]

            for buff, attribute in zip(buffers, attributes, strict=True):
                buff.append(annotation.get(attribute.name))
        # If the all values for a given attribute are
        # empty (i.e. - "."), then that attribute has no
        # values to be written and will be skipped in the output
        has_value = {
            attr.name: any(filter(lambda x: x != ".", buffers[idx]))
            for idx, attr in enumerate(attributes)
        }
        for buff, attribute in zip(buffers, attributes, strict=True):
            if attribute.internal or not has_value[attribute.name]:
                continue
            if vcf_var.header.info[attribute.name].type == "String":
                buff = _VCFWriter._convert_to_string(buff)
            vcf_var.info[attribute.name] = buff

    def __enter__(self) -> _VCFWriter:
        self.output_file = VariantFile(self.path, "w", header=self.header)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during writing vcf: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.output_file.close()

        return exc_type is None

    def filter(self, data: AnnotationsWithSource) -> None:
        data.source.translate(self.header)
        _VCFWriter._update_variant(
            data.source,
            [annotation.context for annotation in data.annotations],
            self.annotation_attributes,
            self.pipeline,
        )
        self.output_file.write(data.source)


class _VCFBatchWriter(Filter):
    """A filter that writes batches of variants to a VCF file."""

    def __init__(
        self,
        path: str,
        pipeline: AnnotationPipeline,
        header: VariantHeader,
    ):
        self.writer = _VCFWriter(path, pipeline, header)

    def __enter__(self) -> _VCFBatchWriter:
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
                "exception during writing vcf: %s, %s, %s",
                exc_type, exc_value, exc_tb)

        self.writer.__exit__(exc_type, exc_value, exc_tb)

        return exc_type is None

    def filter(self, data: Sequence[AnnotationsWithSource]) -> None:
        for variant in data:
            self.writer.filter(variant)


def _annotate_vcf(
    output_path: str,
    pipeline_config: RawAnnotatorsConfig,
    grr_definition: dict,
    region: Region | None,
    args: _ProcessingArgs,
) -> None:
    """Annotate a VCF file using a processing pipeline."""

    pipeline_config_old = None
    if args.reannotate:
        pipeline_config_old = Path(args.reannotate).read_text()

    grr = build_genomic_resource_repository(definition=grr_definition)

    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
        allow_repeated_attributes=args.allow_repeated_attributes,
        work_dir=Path(args.work_dir),
        config_old_raw=pipeline_config_old,
        full_reannotation=args.full_reannotation,
    )

    source: Source
    filters: list[Filter] = []

    if args.batch_size <= 0:
        source = _VCFSource(args.input)
        filters.extend([
            AnnotationPipelineAnnotatablesFilter(pipeline),
            _VCFWriter(output_path, pipeline, source.header),
        ])
    else:
        source = _VCFBatchSource(args.input)
        filters.extend([
            AnnotationPipelineAnnotatablesBatchFilter(pipeline),
            _VCFBatchWriter(output_path, pipeline, source.source.header),
        ])

    with PipelineProcessor(source, filters) as processor:
        processor.process_region(region)


def _concat(partfile_paths: list[str], output_path: str) -> None:
    """Concatenate multiple VCF files into a single VCF file *in order*."""
    # Get any header from the partfiles, they should all be equal
    # and usable as a final output header
    header_donor = VariantFile(partfile_paths[0], "r")
    output_file = VariantFile(output_path, "w", header=header_donor.header)
    for path in partfile_paths:
        partfile = VariantFile(path, "r")
        for variant in partfile.fetch():
            output_file.write(variant)
        partfile.close()
    output_file.close()
    header_donor.close()

    for partfile_path in partfile_paths:
        os.remove(partfile_path)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Construct and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Annotate VCF",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input", default="-", nargs="?",
        help="the input vcf file")
    parser.add_argument(
        "-r", "--region-size", default=300_000_000,
        type=int, help="region size to parallelize by")
    parser.add_argument(
        "-w", "--work-dir",
        help="Directory to store intermediate output files",
        default="annotate_vcf_output")
    parser.add_argument(
        "-o", "--output",
        help="Filename of the output VCF result",
        default=None)
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
    TaskGraphCli.add_arguments(parser)
    VerbosityConfiguration.set_arguments(parser)
    return parser


def _make_vcf_tabix(filepath: str) -> None:
    tabix_index(filepath, preset="vcf")


def _add_tasks_plaintext(
    args: _ProcessingArgs,
    task_graph: TaskGraph,
    output_path: str,
    pipeline_config: RawPipelineConfig,
    grr_definition: dict[str, Any],
) -> None:
    task_graph.create_task(
        "all_variants_annotate",
        _annotate_vcf,
        args=[
            output_path,
            pipeline_config,
            grr_definition,
            None,
            args,
        ],
        deps=[],
    )


def _add_tasks_tabixed(
    args: _ProcessingArgs,
    task_graph: TaskGraph,
    output_path: str,
    pipeline_config: RawPipelineConfig,
    grr_definition: dict[str, Any],
) -> None:
    with closing(TabixFile(args.input)) as pysam_file:
        regions = produce_regions(pysam_file, args.region_size)
    file_paths = produce_partfile_paths(
        args.input, regions, args.work_dir)

    annotation_tasks = []
    for (region, file_path) in zip(regions, file_paths, strict=True):
        annotation_tasks.append(task_graph.create_task(
            f"part-{str(region).replace(':', '-')}",
            _annotate_vcf,
            args=[
                file_path,
                pipeline_config,
                grr_definition,
                region,
                args,
            ],
            deps=[],
        ))

    annotation_sync = task_graph.create_task(
        "sync_vcf_annotate", lambda: None,
        args=[], deps=annotation_tasks,
    )

    concat_task = task_graph.create_task(
        "concat",
        _concat,
        args=[file_paths, output_path],
        deps=[annotation_sync],
    )
    task_graph.create_task(
        "compress_and_tabix",
        _make_vcf_tabix,
        args=[output_path],
        deps=[concat_task])


def cli(raw_args: list[str] | None = None) -> None:
    """Entry point for running the VCF annotation tool."""
    if not raw_args:
        raw_args = sys.argv[1:]

    arg_parser = _build_argument_parser()
    args = vars(arg_parser.parse_args(raw_args))
    if not os.path.exists(args["input"]):
        raise ValueError(f"{args['input']} does not exist!")
    if not os.path.exists(args["work_dir"]):
        os.mkdir(args["work_dir"])
    args["task_status_dir"] = os.path.join(args["work_dir"], ".task-status")
    args["task_log_dir"] = os.path.join(args["work_dir"], ".task-log")

    pipeline, _, grr = get_stuff_from_context(args)
    assert grr.definition is not None

    cache_pipeline_resources(grr, pipeline)

    processing_args = _ProcessingArgs(
        args["input"],
        args["reannotate"],
        args["work_dir"],
        args["batch_size"],
        args["region_size"],
        args["allow_repeated_attributes"],
        args["full_reannotation"],
    )

    output_path = build_output_path(args["input"], args["output"])
    task_graph = TaskGraph()
    if tabix_index_filename(args["input"]):
        _add_tasks_tabixed(
            processing_args,
            task_graph,
            output_path,
            pipeline.raw,
            grr.definition,
        )
    else:
        _add_tasks_plaintext(
            processing_args,
            task_graph,
            output_path,
            pipeline.raw,
            grr.definition,
        )

    add_input_files_to_task_graph(args, task_graph)
    TaskGraphCli.process_graph(task_graph, **args)
