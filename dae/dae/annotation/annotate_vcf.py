from __future__ import annotations

import os
import sys
import argparse
import logging
from contextlib import closing
from typing import List, Optional, Any, Union

from pysam import VariantFile, TabixFile, \
    tabix_index  # pylint: disable=no-name-in-module

from dae.annotation.context import CLIAnnotationContext
from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import AnnotationPipeline, \
    ReannotationPipeline, AnnotatorInfo

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.utils.fs_utils import tabix_index_filename
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.cached_repository import cache_resources
from dae.genomic_resources.repository import GenomicResourceRepo

from dae.genomic_resources.genomic_context import get_genomic_context
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph

logger = logging.getLogger("annotate_vcf")


PART_FILENAME = "{in_file}_annotation_{chrom}_{pos_beg}_{pos_end}.gz"


def configure_argument_parser() -> argparse.ArgumentParser:
    """Construct and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Annotate columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("input", default="-", nargs="?",
                        help="the input vcf file")
    parser.add_argument("pipeline", default="context", nargs="?",
                        help="The pipeline definition file. By default, or if "
                        "the value is gpf_instance, the annotation pipeline "
                        "from the configured gpf instance will be used.")
    parser.add_argument("-r", "--region-size", default=300_000_000,
                        type=int, help="region size to parallelize by")
    parser.add_argument("-w", "--work-dir",
                        help="Directory to store intermediate output files in",
                        default="annotate_vcf_output")
    parser.add_argument("-o", "--output",
                        help="Filename of the output VCF result",
                        default=None)
    parser.add_argument("--reannotate", default=None,
                        help="Old pipeline config to reannotate over")

    CLIAnnotationContext.add_context_arguments(parser)
    TaskGraphCli.add_arguments(parser)
    VerbosityConfiguration.set_arguments(parser)
    return parser


def update_header(
    variant_file: VariantFile,
    pipeline: Union[AnnotationPipeline, ReannotationPipeline]
) -> None:
    """Update a variant file's header with annotation pipeline scores."""
    header = variant_file.header
    header.add_meta("pipeline_annotation_tool", "GPF variant annotation.")
    header.add_meta("pipeline_annotation_tool", f"{' '.join(sys.argv)}")
    if isinstance(pipeline, ReannotationPipeline):
        header_info_keys = variant_file.header.info.keys()
        old_annotation_columns = {
            attr.name for attr in pipeline.pipeline_old.get_attributes()
            if not attr.internal
        }
        new_annotation_columns = {
            attr.name for attr in pipeline.get_attributes()
            if not attr.internal
        }

        for info_key in header_info_keys:
            if info_key in old_annotation_columns \
                    and info_key not in new_annotation_columns:
                variant_file.header.info.remove_header(info_key)

        attributes = []
        for attr in pipeline.get_attributes():
            if attr.internal:
                continue

            if attr.name not in variant_file.header.info:
                attributes.append(attr)
    else:
        attributes = pipeline.get_attributes()

    for attribute in attributes:
        description = attribute.description
        description = description.replace("\n", " ")
        description = description.replace('"', '\\"')
        header.info.add(attribute.name, "A", "String", description)


def cache_pipeline(
    grr: GenomicResourceRepo, pipeline: AnnotationPipeline
) -> None:
    """Cache the resources used by the pipeline."""
    resource_ids: set[str] = set()
    for annotator in pipeline.annotators:
        resource_ids = resource_ids | \
            set(res.resource_id for res in annotator.resources)
    cache_resources(grr, resource_ids)


def build_pipeline(
    pipeline_config: list[AnnotatorInfo],
    allow_repeated_attributes: bool,
    grr: GenomicResourceRepo,
    reannotate: Optional[str] = None,
) -> tuple[AnnotationPipeline, Optional[AnnotationPipeline]]:
    """Build an annotation pipeline from a pipeline config."""
    pipeline = build_annotation_pipeline(
        pipeline_config=pipeline_config,
        grr_repository=grr,
        allow_repeated_attributes=allow_repeated_attributes)
    pipeline_old = None
    if reannotate:
        pipeline_old = build_annotation_pipeline(
            pipeline_config_file=reannotate,
            grr_repository=grr,
            allow_repeated_attributes=allow_repeated_attributes
        )
        pipeline_new = pipeline
        pipeline = ReannotationPipeline(pipeline_new, pipeline_old)

    return pipeline, pipeline_old


def annotate(  # pylint: disable=too-many-locals,too-many-branches
    input_file: str,
    region: Optional[tuple[str, int, int]],
    pipeline_config: list[AnnotatorInfo],
    grr_definition: Optional[dict],
    out_file_path: str,
    allow_repeated_attributes: bool,
    reannotate: Optional[str] = None,
) -> None:
    # flake8: noqa: C901
    """Annotate a region from a given input VCF file using a pipeline."""
    grr = build_genomic_resource_repository(definition=grr_definition)
    pipeline, _ = build_pipeline(
        pipeline_config=pipeline_config,
        grr=grr,
        allow_repeated_attributes=allow_repeated_attributes,
        reannotate=reannotate
    )

    with closing(VariantFile(input_file)) as in_file:
        update_header(in_file, pipeline)
        with pipeline.open(), closing(VariantFile(
            out_file_path, "w", header=in_file.header
        )) as out_file:
            annotation_attributes = pipeline.get_attributes()

            if region is None:
                in_file_iter = in_file.fetch()
            else:
                in_file_iter = in_file.fetch(*region)

            for vcf_var in in_file_iter:
                # pylint: disable=use-list-literal
                buffers: List[List] = [list() for _ in annotation_attributes]

                if vcf_var.ref is None:
                    logger.warning(
                        "vcf variant without reference: %s %s",
                        vcf_var.chrom, vcf_var.pos
                    )
                    continue

                if vcf_var.alts is None:
                    logger.info(
                        "vcf variant without alternatives: %s %s",
                        vcf_var.chrom, vcf_var.pos
                    )
                    continue

                has_value = {}

                if isinstance(pipeline, ReannotationPipeline):
                    for col in pipeline.attributes_deleted:
                        del vcf_var.info[col]

                for alt in vcf_var.alts:
                    if isinstance(pipeline, ReannotationPipeline):
                        annotation = pipeline.annotate(
                            VCFAllele(
                                vcf_var.chrom, vcf_var.pos, vcf_var.ref, alt
                            ), dict(vcf_var.info)
                        )
                    else:
                        annotation = pipeline.annotate(
                            VCFAllele(
                                vcf_var.chrom, vcf_var.pos, vcf_var.ref, alt
                            )
                        )

                    for buff, attribute in zip(buffers, annotation_attributes):
                        attr = annotation.get(attribute.name)
                        attr = attr if attr is not None else "."
                        if attr != ".":
                            has_value[attribute.name] = True
                        if isinstance(attr, list):
                            attr = ";".join(map(str, attr))
                        elif isinstance(attr, dict):
                            attr = ";".join(
                                f"{k}:{v}"
                                for k, v in attr.items()
                            )
                        attr = str(attr).replace(";", "|")\
                                        .replace(",", "|")\
                                        .replace(" ", "_")
                        buff.append(attr)

                for attribute, buff in zip(annotation_attributes, buffers):
                    if has_value.get(attribute.name, False):
                        vcf_var.info[attribute.name] = buff
                out_file.write(vcf_var)


def combine(
    input_file_path: str,
    pipeline_config: Optional[list[AnnotatorInfo]],
    grr_definition: Optional[dict],
    partfile_paths: List[str],
    output_file_path: str
) -> None:
    """Combine annotated region parts into a single VCF file."""
    pipeline = build_annotation_pipeline(
        pipeline_config=pipeline_config,
        grr_repository_definition=grr_definition)

    with closing(VariantFile(input_file_path)) as input_file:
        update_header(input_file, pipeline)
        with closing(
            VariantFile(output_file_path, "w", header=input_file.header)
        ) as output_file:
            for partfile_path in partfile_paths:
                partfile = VariantFile(partfile_path)
                for rec in partfile.fetch():
                    output_file.write(rec)
        tabix_index(output_file_path, preset="vcf")

    for partfile_path in partfile_paths:
        os.remove(partfile_path)


def get_chromosome_length(
    tabix_file: TabixFile, chrom: str, step: int = 100_000_000
) -> int:
    # TODO Eventually this should be extracted as a util
    """Return the length of a chromosome (or contig).

    Returned value is guaranteed to be larger than the actual contig length.
    """
    def any_records(riter: Any) -> bool:
        try:
            next(riter)
        except StopIteration:
            return False

        return True

    # First we find any region that includes the last record i.e.
    # the length of the chromosome
    left, right = None, None
    pos = step
    while left is None or right is None:
        if any_records(tabix_file.fetch(chrom, pos, None)):
            left = pos
            pos = pos * 2
        else:
            right = pos
            pos = pos // 2
    # Second we use binary search to narrow the region until we find the
    # index of the last element (in left) and the length (in right)
    while (right - left) > 5_000_000:
        pos = (left + right) // 2
        if any_records(tabix_file.fetch(chrom, pos, None)):
            left = pos
        else:
            right = pos
    return right


def produce_regions(
    pysam_file: TabixFile, region_size: int
) -> list[tuple[str, int, int]]:
    """Given a region size, produce contig regions to annotate by."""
    contig_lengths = {}
    for contig in map(str, pysam_file.contigs):
        contig_lengths[contig] = get_chromosome_length(pysam_file, contig)
    return [
        (contig, start, start + region_size)
        for contig, length in contig_lengths.items()
        for start in range(1, length, region_size)
    ]


def produce_partfile_paths(
    input_file_path: str, regions: list[tuple[str, int, int]], work_dir: str
) -> list[str]:
    """Produce a list of file paths for output region part files."""
    filenames = []
    for region in regions:
        pos_beg = region[1] if len(region) > 1 else "_"
        pos_end = region[2] if len(region) > 2 else "_"
        filenames.append(os.path.join(work_dir, PART_FILENAME.format(
            in_file=os.path.basename(input_file_path),
            chrom=region[0], pos_beg=pos_beg, pos_end=pos_end
        )))
    return filenames


def cli(raw_args: Optional[list[str]] = None) -> None:
    """Run command line interface for annotate_vcf tool."""
    if not raw_args:
        raw_args = sys.argv[1:]

    parser = configure_argument_parser()
    args = parser.parse_args(raw_args)
    VerbosityConfiguration.set(args)
    CLIAnnotationContext.register(args)

    context = get_genomic_context()
    pipeline = CLIAnnotationContext.get_pipeline(context)
    grr = CLIAnnotationContext.get_genomic_resources_repository(context)
    if grr is None:
        raise ValueError("No valid GRR configured. Aborting.")

    if args.output:
        output = args.output
    else:
        output = os.path.basename(args.input).split(".")[0] + "_annotated.vcf"

    if not os.path.exists(args.work_dir):
        os.mkdir(args.work_dir)

    # cache pipeline
    cache_pipeline(grr, pipeline)

    task_graph = TaskGraph()

    task_graph.input_files.append(args.input)
    task_graph.input_files.append(args.pipeline)
    if args.reannotate:
        task_graph.input_files.append(args.reannotate)

    if not tabix_index_filename(args.input):
        assert grr is not None
        task_graph.create_task(
            "all_variants_annotate",
            annotate,
            [args.input, None, pipeline.get_info(),
             grr.definition, output, args.allow_repeated_attributes,
             args.reannotate],
            []
        )
    else:
        with closing(TabixFile(args.input)) as pysam_file:
            regions = produce_regions(pysam_file, args.region_size)
        file_paths = produce_partfile_paths(args.input, regions, args.work_dir)
        region_tasks = []
        for index, (region, file_path) in enumerate(zip(regions, file_paths)):
            assert grr is not None
            region_tasks.append(task_graph.create_task(
                f"part-{index}",
                annotate,
                [args.input, region,
                 pipeline.get_info(), grr.definition,
                 file_path, args.allow_repeated_attributes, args.reannotate],
                []
            ))

        assert grr is not None
        task_graph.create_task(
            "combine",
            combine,
            [args.input, pipeline.get_info(),
             grr.definition, file_paths, output],
            region_tasks
        )

    args.task_status_dir = os.path.join(args.work_dir, ".task-status")
    args.log_dir = os.path.join(args.work_dir, ".task-log")

    TaskGraphCli.process_graph(task_graph, **vars(args))


if __name__ == "__main__":
    cli(sys.argv[1:])
