from __future__ import annotations

import sys
import argparse
import logging
import glob
from typing import List, Optional

from pysam import VariantFile, TabixFile  # pylint: disable=no-name-in-module

from dae.annotation.context import CLIAnnotationContext
from dae.annotation.annotatable import VCFAllele
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.genomic_resources.genomic_context import get_genomic_context
from dae.task_graph import TaskGraphCli
from dae.task_graph.graph import TaskGraph

logger = logging.getLogger("annotate_vcf")


# TODO Make unit test for multiallelic vcf input


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
    parser.add_argument("output", default="-", nargs="?",
                        help="the output column file")
    parser.add_argument("region_size", default=500,
                        type=int, help="region size to parallelize by")

    CLIAnnotationContext.add_context_arguments(parser)
    TaskGraphCli.add_arguments(parser)
    VerbosityConfiguration.set_argumnets(parser)
    return parser


def annotate(input_file, region, pipeline):
    # once again open the VCF file
    # query variants from it for given region
    # annotate them and yield them how?
    # handling the variants
    in_file = VariantFile(input_file)
    update_header(in_file, pipeline)
    annotation_attributes = pipeline.annotation_schema.names
    out_file = VariantFile(
        f"output/{input_file}_annotation_{region[0]}_{region[1]}_{region[2]}",
        "w",
        header=in_file.header
    )
    with pipeline.open():
        for vcf_var in in_file.fetch(*region):
            # pylint: disable=use-list-literal
            buffers: List[List] = [list() for _ in annotation_attributes]

            if vcf_var.alts is None:
                logger.info("vcf variant without alternatives: %s", vcf_var)
                continue

            for alt in vcf_var.alts:
                annotabale = VCFAllele(
                    vcf_var.chrom, vcf_var.pos, vcf_var.ref, alt)
                annotation = pipeline.annotate(annotabale)
                for buff, attribute in zip(buffers, annotation_attributes):
                    # TODO Ask what value to use for missing attr
                    buff.append(str(annotation.get(attribute, "-")))

            for attribute, buff in zip(annotation_attributes, buffers):
                vcf_var.info[attribute] = ",".join(buff)
            out_file.write(vcf_var)
    out_file.close()
    in_file.close()


def combine(input_file, pipeline):
    input_file = VariantFile(input_file)
    update_header(input_file, pipeline)
    with VariantFile("output/combined", "w", header=input_file.header) as out:
        for part_filename in glob.glob("output/*_annotation_*"):
            part_file = VariantFile(part_filename)
            for rec in part_file.fetch():
                out.write(rec)
    input_file.close()


def update_header(variant_file, pipeline):
    header = variant_file.header
    header.add_meta(
        "pipeline_annotation_tool", "GPF variant annotation."
    )
    header.add_meta(
        "pipeline_annotation_tool", f"{' '.join(sys.argv)}")
    for attribute in pipeline.annotation_schema.names:
        description = pipeline.annotation_schema[attribute].description
        description = description.replace("\n", " ")
        header.info.add(attribute, "A", "String", description)


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

    if args.output == "-":
        out_file = sys.stdout
    else:
        # pylint: disable=consider-using-with
        out_file = open(args.output, "wt")

    with TabixFile(args.input) as pysam_file:
        contigs = list(map(str, pysam_file.contigs))

    ref_genome = context.get_reference_genome()
    assert ref_genome is not None
    contig_lengths = {}
    for contig in contigs:
        try:
            contig_lengths[contig] = ref_genome.get_chrom_length(contig)
        except ValueError as exc:
            # TODO Handle missing chromosomes by queueing them as an
            # entire region by themselves
            print(str(exc))
    # TODO Use utils/regions and create func for building regions.
    # genomic resources - genomic_scores.py _split_into_regions
    # make it cover both use cases and extract as util
    regions = [
        (contig, start, start + args.region_size)
        for contig, length in contig_lengths.items()
        for start in range(1, length, args.region_size)
    ]
    task_graph = TaskGraph()
    parts = [
        task_graph.create_task(
            f"part-{index}", annotate,
            [args.input, region, pipeline], []
        )
        for index, region in enumerate(regions)
    ]
    task_graph.create_task("combine", combine, [args.input, pipeline], [])
    TaskGraphCli.process_graph(task_graph, **vars(args))

    if args.output != "-":
        out_file.close()


if __name__ == "__main__":
    cli(sys.argv[1:])
