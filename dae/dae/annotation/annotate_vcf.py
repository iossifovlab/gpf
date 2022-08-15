from __future__ import annotations

import sys
import argparse
import logging
from typing import List

from pysam import VariantFile  # pylint: disable=no-name-in-module

from dae.annotation.context import CLIAnnotationContext
from dae.annotation.annotatable import VCFAllele
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.genomic_resources.genomic_context import get_genomic_context

logger = logging.getLogger("annotate_vcf")


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

    CLIAnnotationContext.add_context_arguments(parser)
    VerbosityConfiguration.set_argumnets(parser)
    return parser


def cli(raw_args: list[str] = None) -> None:
    """Run command line interface for annotate_vcf tool."""
    # FIXME:
    # pylint: disable=too-many-locals
    if not raw_args:
        raw_args = sys.argv[1:]

    parser = configure_argument_parser()
    args = parser.parse_args(raw_args)
    VerbosityConfiguration.set(args)
    CLIAnnotationContext.register(args)

    context = get_genomic_context()
    pipeline = CLIAnnotationContext.get_pipeline(context)
    annotation_attributes = pipeline.annotation_schema.names

    in_file = VariantFile(args.input)

    if args.output == "-":
        out_file = sys.stdout
    else:
        # pylint: disable=consider-using-with
        out_file = open(args.output, "wt")

    # handling the header
    header = in_file.header
    header.add_meta(
        "pipeline_annotation_tool", "GPF variant annotation."
    )
    header.add_meta(
        "pipeline_annotation_tool", f"{' '.join(sys.argv)}")
    for attribute in annotation_attributes:
        description = pipeline.annotation_schema[attribute].description
        description = description.replace("\n", " ")
        header.info.add(
            attribute, "A", "String",
            description)

    print(str(header), file=out_file, end="")

    # handling the variants
    for vcf_var in in_file:
        buffers: List[List] = [list([]) for _ in annotation_attributes]

        if vcf_var.alts is None:
            logger.info("vcf variant without alternatives: %s", vcf_var)
            continue

        for alt in vcf_var.alts:
            annotabale = VCFAllele(
                vcf_var.chrom, vcf_var.pos, vcf_var.ref, alt)
            annotation = pipeline.annotate(annotabale)
            for buff, attribute in zip(buffers, annotation_attributes):
                buff.append(str(annotation[attribute]))

        for attribute, buff in zip(annotation_attributes, buffers):
            vcf_var.info[attribute] = ",".join(buff)
        print(str(vcf_var), file=out_file, end="")

    in_file.close()

    if args.output != "-":
        out_file.close()


if __name__ == "__main__":
    cli(sys.argv[1:])
