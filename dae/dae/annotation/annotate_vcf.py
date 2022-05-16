from __future__ import annotations

import sys
import argparse

from typing import List

from dae.annotation.context import Context
from dae.annotation.annotatable import VCFAllele
from dae.genomic_resources.cli import VerbosityConfiguration
from pysam import VariantFile  # type: ignore


def configure_argument_parser() -> argparse.ArgumentParser:
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

    Context.add_context_arguments(parser)
    VerbosityConfiguration.set_argumnets(parser)
    return parser


def cli(raw_args: list[str] = None) -> None:
    if not raw_args:
        raw_args = sys.argv[1:]

    parser = configure_argument_parser()
    args = parser.parse_args(raw_args)
    VerbosityConfiguration.set(args)
    context = Context(args)

    pipeline = context.get_pipeline()
    annotation_attributes = pipeline.annotation_schema.names

    in_file = VariantFile(args.input)

    if args.output == "-":
        out_file = sys.stdout
    else:
        out_file = open(args.output, "wt")

    # handling the header
    header = in_file.header
    header.add_meta(
        "pipeline_annotation_tool", "GPF variant annotation."
    )
    header.add_meta(
        "pipeline_annotation_tool", '"{}"'.format(" ".join(sys.argv))
    )
    for aa in annotation_attributes:
        header.info.add(aa, "A", "String",
                        pipeline.annotation_schema[aa].description)

    print(str(header), file=out_file, end="")

    # handling the variants
    for var in in_file:
        buffers: List[List] = [list([]) for _ in annotation_attributes]

        for alt in var.alts:
            annotabale = VCFAllele(var.chrom, var.pos, var.ref, alt)
            annotation = pipeline.annotate(annotabale)
            for buff, aa in zip(buffers, annotation_attributes):
                buff.append(str(annotation[aa]))

        for aa, buff in zip(annotation_attributes, buffers):
            var.info[aa] = ",".join(buff)
        print(str(var), file=out_file, end="")

    in_file.close()

    if args.output != "-":
        out_file.close()


if __name__ == "__main__":
    cli(sys.argv[1:])
