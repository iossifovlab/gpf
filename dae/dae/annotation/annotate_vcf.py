from __future__ import annotations

import os
import sys
import argparse
import logging
from contextlib import closing
from typing import List, Optional

from pysam import VariantFile, TabixFile, \
    tabix_index  # pylint: disable=no-name-in-module

from dae.annotation.context import CLIAnnotationContext
from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import build_annotation_pipeline

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.utils.fs_utils import tabix_index_filename
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.genomic_resources.cached_repository import cache_resources
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph

logger = logging.getLogger("annotate_vcf")


PART_FILENAME = "{in_file}_annotation_{chrom}_{pos_beg}_{pos_end}.vcf.gz"


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
    CLIAnnotationContext.add_context_arguments(parser)
    TaskGraphCli.add_arguments(parser)
    VerbosityConfiguration.set_argumnets(parser)
    return parser


def update_header(variant_file, pipeline):
    """Update a variant file's header with annotation pipeline scores."""
    header = variant_file.header
    header.add_meta("pipeline_annotation_tool", "GPF variant annotation.")
    header.add_meta("pipeline_annotation_tool", f"{' '.join(sys.argv)}")
    for attribute in pipeline.annotation_schema.names:
        description = pipeline.annotation_schema[attribute].description
        description = description.replace("\n", " ")
        header.info.add(attribute, "A", "String", description)


def annotate(
        input_file, region, pipeline_config, grr_definition, out_file_path):
    """Annotate a region from a given input VCF file using a pipeline."""
    grr = build_genomic_resource_repository(definition=grr_definition)

    pipeline = build_annotation_pipeline(
        pipeline_config=pipeline_config,
        grr_repository=grr)

    # cache pipeline
    resources: set[str] = set()
    for annotator in pipeline.annotators:
        resources = resources | {res.get_id() for res in annotator.resources}
    cache_resources(grr, resources)

    with closing(VariantFile(input_file)) as in_file:
        update_header(in_file, pipeline)
        with pipeline.open(), closing(VariantFile(
            out_file_path, "w", header=in_file.header
        )) as out_file:
            annotation_attributes = pipeline.annotation_schema.names
            for vcf_var in in_file.fetch(*region):
                # pylint: disable=use-list-literal
                buffers: List[List] = [list() for _ in annotation_attributes]

                if vcf_var.alts is None:
                    logger.info(
                        "vcf variant without alternatives: %s %s",
                        vcf_var.chrom, vcf_var.pos
                    )
                    continue

                for alt in vcf_var.alts:
                    annotation = pipeline.annotate(
                        VCFAllele(vcf_var.chrom, vcf_var.pos, vcf_var.ref, alt)
                    )
                    for buff, attribute in zip(buffers, annotation_attributes):
                        # TODO Ask what value to use for missing attr
                        buff.append(str(annotation.get(attribute, "-")))

                for attribute, buff in zip(annotation_attributes, buffers):
                    vcf_var.info[attribute] = buff
                out_file.write(vcf_var)


def combine(
        input_file_path, pipeline_config, grr_definition,
        partfile_paths, output_file_path):
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


def get_chromosome_length(tabix_file, chrom, step=100_000_000):
    # TODO Eventually this should be extracted as a util
    """Return the length of a chromosome (or contig).

    Returned value is guaranteed to be larger than the actual contig length.
    """
    def any_records(riter):
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


def produce_regions(pysam_file, region_size):
    """Given a region size, produce contig regions to annotate by."""
    contig_lengths = {}
    for contig in map(str, pysam_file.contigs):
        contig_lengths[contig] = get_chromosome_length(pysam_file, contig)
    return [
        (contig, start, start + region_size)
        for contig, length in contig_lengths.items()
        for start in range(1, length, region_size)
    ]


def produce_partfile_paths(input_file_path, regions, work_dir):
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

    if args.output:
        output = args.output
    else:
        output = os.path.basename(args.input).split(".")[0] + "_annotated.vcf"

    if not os.path.exists(args.work_dir):
        os.mkdir(args.work_dir)

    def run_parallelized():
        with closing(TabixFile(args.input)) as pysam_file:
            regions = produce_regions(pysam_file, args.region_size)
        file_paths = produce_partfile_paths(args.input, regions, args.work_dir)
        task_graph = TaskGraph()
        region_tasks = []
        for index, (region, file_path) in enumerate(zip(regions, file_paths)):
            assert grr is not None
            region_tasks.append(task_graph.create_task(
                f"part-{index}",
                annotate,
                [args.input, region,
                 pipeline.config, grr.definition, file_path],
                []
            ))

        assert grr is not None
        task_graph.create_task(
            "combine",
            combine,
            [args.input, pipeline.config, grr.definition, file_paths, output],
            region_tasks
        )

        args.task_status_dir = os.path.join(args.work_dir, "tasks-status")
        args.log_dir = os.path.join(args.work_dir, "tasks-log")

        TaskGraphCli.process_graph(task_graph, **vars(args))

    def run_sequentially():
        assert grr is not None
        annotate(args.input, tuple(), pipeline.config, grr.definition, output)

    if tabix_index_filename(args.input):
        run_parallelized()
    else:
        run_sequentially()


if __name__ == "__main__":
    cli(sys.argv[1:])
