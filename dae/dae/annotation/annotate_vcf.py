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
    tabix_compress,
    tabix_index,
)

from dae.annotation.annotatable import VCFAllele
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
    ReannotationPipeline,
)
from dae.annotation.processing_pipeline import (
    Annotation,
    AnnotationPipelineAnnotatablesBatchFilter,
    AnnotationPipelineAnnotatablesFilter,
    AnnotationsWithSource,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.task_graph.cli_tools import TaskGraphCli
from dae.task_graph.graph import TaskGraph, sync_tasks
from dae.utils.fs_utils import tabix_index_filename
from dae.utils.processing_pipeline import Filter, PipelineProcessor, Source
from dae.utils.regions import Region
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("annotate_vcf")


@dataclass
class _InfoField:
    name: str
    number: str | None
    type: str | None
    description: str | None


class _VCFSource(Source):
    """Source for reading from VCF files."""

    def __init__(self, path: str):
        self.path = path
        self.vcf: VariantFile
        with VariantFile(self.path, "r") as infile:
            self.header = infile.header
        self.info = {
            k: _InfoField(
                name=v.name,
                number=v.number,
                type=v.type,
                description=v.description,
            )
            for k, v in self.header.info.items()
        }

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

    def _convert_info(self, alt_idx: int, variant: VariantRecord) -> dict:
        result = {}
        for k in variant.info:
            if self.info[k].number == "A":
                result[k] = variant.info[k][alt_idx]
            elif self.info[k].number == "1":
                result[k] = variant.info[k]
            elif self.info[k].number == ".":
                result[k] = None
            else:
                result[k] = variant.info[k]
        return result

    def _convert(
        self, variant: VariantRecord,
    ) -> AnnotationsWithSource:
        annotations = [
            Annotation(
                VCFAllele(variant.chrom,
                          variant.pos,
                          variant.ref,  # type: ignore
                          alt),
                self._convert_info(idx, variant),
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
            assert region.start is not None
            in_file_iter = self.vcf.fetch(region.chrom,
                                          region.start - 1,
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

            yield self._convert(vcf_var)


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
        header: VariantHeader,
        annotation_attributes: Sequence[AttributeInfo],
        attributes_to_delete: Sequence[str],
    ):
        self.path = path
        self.output_file: VariantFile
        self.header = self._update_header(
            header, annotation_attributes, attributes_to_delete)
        self.annotation_attributes = annotation_attributes
        self.attributes_to_delete = attributes_to_delete

    @staticmethod
    def _update_header(
        header: VariantHeader,
        annotation_attributes: Sequence[AttributeInfo],
        attributes_to_delete: Sequence[str],
    ) -> VariantHeader:
        """Update a variant file's header with annotation."""
        header.add_meta("pipeline_annotation_tool", "GPF variant annotation.")

        annotation_attr_names = [attr.name for attr in annotation_attributes]

        for info_key in header.info:
            if info_key in attributes_to_delete \
               and info_key not in annotation_attr_names:
                header.info.remove_header(info_key)

        attributes = [
            attr for attr in annotation_attributes
            if attr.name not in header.info
        ]

        for attribute in attributes:
            description = attribute.description
            description = description.replace("\n", " ")
            description = description.replace('"', '\\"')
            header.info.add(attribute.name, "A", "String", description)

        return header

    @staticmethod
    def _convert_to_string(attr: Any) -> str:
        if isinstance(attr, list):
            attr = ";".join(stringify(a, vcf=True) for a in attr)
        elif isinstance(attr, dict):
            attr = ";".join(
                f"{k}:{v}"
                for k, v in attr.items()
            )
        return stringify(attr, vcf=True) \
            .replace(";", "|") \
            .replace(",", "|") \
            .replace(" ", "_")

    @staticmethod
    def _update_variant(
        vcf_var: VariantRecord,
        allele_annotations: list[dict],
        attributes: Sequence[AttributeInfo],
        attributes_to_delete: Sequence[str],
    ) -> None:
        buffers: list[list] = [[] for _ in attributes]

        for col in attributes_to_delete:
            del vcf_var.info[col]

        for annotation in allele_annotations:
            for buff, attribute in zip(buffers, attributes, strict=True):
                value = annotation.get(attribute.name)
                if vcf_var.header.info[attribute.name].type == "String":
                    value = _VCFWriter._convert_to_string(value)
                buff.append(value)
        # If the all values for a given attribute are
        # empty (i.e. - "."), then that attribute has no
        # values to be written and will be skipped in the output
        has_value = {
            attr.name: len(list(filter(lambda x: x != ".", buffers[idx])))
            for idx, attr in enumerate(attributes)
        }
        for buff, attribute in zip(buffers, attributes, strict=True):
            if not has_value[attribute.name]:
                continue
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
            self.attributes_to_delete,
        )
        self.output_file.write(data.source)


class _VCFBatchWriter(Filter):
    """A filter that writes batches of variants to a VCF file."""

    def __init__(
        self,
        path: str,
        header: VariantHeader,
        annotation_attributes: Sequence[AttributeInfo],
        attributes_to_delete: Sequence[str],
    ):
        self.writer = _VCFWriter(
            path, header, annotation_attributes, attributes_to_delete)

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
    args: dict[str, Any],
) -> None:
    """Annotate a VCF file using a processing pipeline."""
    build_cli_genomic_context(args)
    grr = build_genomic_resource_repository(definition=grr_definition)

    pipeline_previous = None
    if args["reannotate"]:
        pipeline_previous = load_pipeline_from_file(args["reannotate"], grr)

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

    annotation_attributes = [
        attr for attr in pipeline.get_attributes()
        if not attr.internal
    ]

    source: Source
    filters: list[Filter] = []

    if args["batch_size"] <= 0:
        source = _VCFSource(args["input"])
        header = source.header.copy()
        filters.extend([
            AnnotationPipelineAnnotatablesFilter(pipeline),
            _VCFWriter(output_path,
                       header,
                       annotation_attributes,
                       attributes_to_delete),
        ])
    else:
        source = _VCFBatchSource(args["input"], batch_size=args["batch_size"])
        header = source.source.header.copy()
        filters.extend([
            AnnotationPipelineAnnotatablesBatchFilter(pipeline),
            _VCFBatchWriter(output_path,
                            header,
                            annotation_attributes,
                            attributes_to_delete),
        ])

    with PipelineProcessor(source, filters) as processor:
        processor.process_region(region)


def _concat(
    partfile_paths: list[str],
    output_path: str,
    keep_parts: bool,  # noqa: FBT001
) -> None:
    """Concatenate multiple VCF files into a single VCF file *in order*."""
    # Get any header from the partfiles, they should all be equal
    # and usable as a final output header
    header_donor = VariantFile(partfile_paths[0], "r")
    output_file = VariantFile(
        output_path, "w",
        header=header_donor.header.copy(),
    )
    for path in partfile_paths:
        partfile = VariantFile(path, "r")
        for variant in partfile.fetch():
            output_file.write(variant)
        partfile.close()
    output_file.close()
    header_donor.close()

    if not keep_parts:
        for partfile_path in partfile_paths:
            os.remove(partfile_path)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Construct and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Annotate VCF",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_annotation_arguments(parser)
    return parser


def _tabix_index(filepath: str) -> None:
    tabix_index(filepath, preset="vcf", force=True)


def _tabix_compress(filepath: str) -> None:
    tabix_compress(filepath, f"{filepath}.gz", force=True)


def _add_tasks_plaintext(
    args: dict[str, Any],
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
    args: dict[str, Any],
    task_graph: TaskGraph,
    output_path: str,
    pipeline_config: RawPipelineConfig,
    grr_definition: dict[str, Any],
) -> None:
    with closing(TabixFile(args["input"])) as pysam_file:
        regions = produce_regions(pysam_file, args["region_size"])
    file_paths = produce_partfile_paths(
        args["input"], regions, args["work_dir"])

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
        "sync_vcf_annotate", sync_tasks,
        args=[], deps=annotation_tasks,
    )

    concat_task = task_graph.create_task(
        "concat",
        _concat,
        args=[file_paths, output_path, args["keep_parts"]],
        deps=[annotation_sync],
    )
    compress_task = task_graph.create_task(
        "tabix_compress",
        _tabix_compress,
        args=[output_path],
        deps=[concat_task])

    task_graph.create_task(
        "tabix_index",
        _tabix_index,
        args=[f"{output_path}.gz"],
        deps=[compress_task])


def cli(argv: list[str] | None = None) -> None:
    """Entry point for running the VCF annotation tool."""
    if not argv:
        argv = sys.argv[1:]

    arg_parser = _build_argument_parser()
    args = vars(arg_parser.parse_args(argv))
    VerbosityConfiguration.set_verbosity(args["verbose"])

    args = handle_default_args(args)

    context = build_cli_genomic_context(args)
    pipeline = get_pipeline_from_context(context)
    grr = get_grr_from_context(context)
    assert grr.definition is not None

    cache_pipeline_resources(grr, pipeline)

    output_path = args["output"]
    region_size = args["region_size"]

    task_graph = TaskGraph()
    if tabix_index_filename(args["input"]) and region_size > 0:
        _add_tasks_tabixed(
            args,
            task_graph,
            output_path,
            pipeline.raw,
            grr.definition,
        )
    else:
        _add_tasks_plaintext(
            args,
            task_graph,
            output_path,
            pipeline.raw,
            grr.definition,
        )

    add_input_files_to_task_graph(args, task_graph)
    TaskGraphCli.process_graph(task_graph, **args)
