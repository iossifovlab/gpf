from __future__ import annotations

import os
import sys
import argparse
import logging
from typing import List, Optional

from pysam import VariantFile, TabixFile  # pylint: disable=no-name-in-module

from dae.annotation.context import CLIAnnotationContext
from dae.annotation.annotatable import VCFAllele
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.utils.fs_utils import tabix_index_filename
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph

logger = logging.getLogger("annotate_vcf")


# TODO Make unit test for multiallelic vcf input


PART_FILENAME = "{in_file}_annotation_{chrom}_{pos_beg}_{pos_end}.vcf"
COMBINED_FILENAME = "combined.vcf"


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
    parser.add_argument("-o", "--work-dir",
                        help="Directory to store intermediate output files in",
                        default="output")
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


def annotate(input_file, region, pipeline, out_filepath):
    """Annotate a region from a given input VCF file using a pipeline."""
    in_file = VariantFile(input_file)
    update_header(in_file, pipeline)
    out_file = VariantFile(out_filepath, "w", header=in_file.header)
    annotation_attributes = pipeline.annotation_schema.names
    with pipeline.open():
        for vcf_var in in_file.fetch(*region):
            # pylint: disable=use-list-literal
            buffers: List[List] = [list() for _ in annotation_attributes]

            if vcf_var.alts is None:
                logger.info("vcf variant without alternatives: %s", vcf_var)
                continue

            for alt in vcf_var.alts:
                annotation = pipeline.annotate(
                    VCFAllele(vcf_var.chrom, vcf_var.pos, vcf_var.ref, alt)
                )
                for buff, attribute in zip(buffers, annotation_attributes):
                    # TODO Ask what value to use for missing attr
                    buff.append(str(annotation.get(attribute, "-")))

            for attribute, buff in zip(annotation_attributes, buffers):
                vcf_var.info[attribute] = ",".join(buff)
            out_file.write(vcf_var)
    out_file.close()
    in_file.close()


def combine(input_filepath, pipeline, regions, work_dir):
    """Combine annotated regions into a single VCF file."""
    input_file = VariantFile(input_filepath)
    update_header(input_file, pipeline)
    output_filepath = os.path.join(work_dir, COMBINED_FILENAME)
    with VariantFile(output_filepath, "w", header=input_file.header) as out:
        # we re-construct the filenames from the regions in order to
        # preserve the ordering of the variants by position
        for region in regions:
            part_filename = os.path.join(work_dir, PART_FILENAME.format(
                in_file=input_filepath,
                chrom=region[0], pos_beg=region[1], pos_end=region[2]
            ))
            part_file = VariantFile(part_filename)
            for rec in part_file.fetch():
                out.write(rec)
    input_file.close()


def produce_regions(context, contigs, region_size):
    """Given a region size, produce contig regions to annotate by."""
    ref_genome = context.get_reference_genome()
    assert ref_genome is not None
    contig_lengths = {}
    unknown_contigs = []
    for contig in contigs:
        try:
            contig_lengths[contig] = ref_genome.get_chrom_length(contig)
        except ValueError:
            logger.warning(
                "Could not find contig %s in reference genome", contig
            )
            unknown_contigs.append((contig,))
    return [
        (contig, start, start + region_size)
        for contig, length in contig_lengths.items()
        for start in range(1, length, region_size)
    ] + unknown_contigs


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

    assert not os.path.exists(args.work_dir)
    os.mkdir(args.work_dir)

    def run_parallelized():
        with TabixFile(args.input) as pysam_file:
            contigs = list(map(str, pysam_file.contigs))
        regions = produce_regions(context, contigs, args.region_size)

        task_graph = TaskGraph()
        for index, region in enumerate(regions):
            out_filepath = os.path.join(args.work_dir, PART_FILENAME.format(
                in_file=args.input,
                chrom=region[0], pos_beg=region[1], pos_end=region[2]
            ))
            task_graph.create_task(
                f"part-{index}", annotate,
                [args.input, region, pipeline, out_filepath], []
            )
        task_graph.create_task(
            "combine", combine,
            [args.input, pipeline, regions, args.work_dir], []
        )
        TaskGraphCli.process_graph(task_graph, **vars(args))

    def run_sequentially():
        annotate(
            args.input, tuple(), pipeline,
            os.path.join(args.work_dir, COMBINED_FILENAME)
        )

    if tabix_index_filename(args.input):
        run_parallelized()
    else:
        run_sequentially()


if __name__ == "__main__":
    cli(sys.argv[1:])
