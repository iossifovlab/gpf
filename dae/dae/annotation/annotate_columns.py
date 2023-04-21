from __future__ import annotations
import logging
import sys
import gzip
import argparse
from typing import Optional

from dae.annotation.context import CLIAnnotationContext
from dae.annotation.record_to_annotatable import build_record_to_annotatable
from dae.annotation.record_to_annotatable import \
    add_record_to_annotable_arguments
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.genomic_resources.genomic_context import get_genomic_context

logger = logging.getLogger("annotate_columns")


def configure_argument_parser() -> argparse.ArgumentParser:
    """Configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Annotate columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("input", default="-", nargs="?",
                        help="the input column file")
    parser.add_argument("pipeline", default="context", nargs="?",
                        help="The pipeline definition file. By default, or if "
                        "the value is gpf_instance, the annotation pipeline "
                        "from the configured gpf instance will be used.")
    parser.add_argument("output", default="-", nargs="?",
                        help="the output column file")

    parser.add_argument("-in_sep", "--input-separator", default="\t",
                        help="The column separator in the input")
    parser.add_argument("-out_sep", "--output-separator", default="\t",
                        help="The column separator in the output")
    CLIAnnotationContext.add_context_arguments(parser)
    add_record_to_annotable_arguments(parser)
    VerbosityConfiguration.set_argumnets(parser)
    return parser


def cli(raw_args: Optional[list[str]] = None) -> None:
    """Run command line interface for annotate columns."""
    if raw_args is None:
        raw_args = sys.argv[1:]

    parser = configure_argument_parser()
    args = parser.parse_args(raw_args)
    VerbosityConfiguration.set(args)
    CLIAnnotationContext.register(args)

    context = get_genomic_context()
    pipeline = CLIAnnotationContext.get_pipeline(context)
    annotation_attributes = pipeline.annotation_schema.public_fields

    if args.input == "-":
        in_file = sys.stdin
    elif args.input.endswith(".gz"):
        # pylint: disable=consider-using-with
        in_file = gzip.open(args.input, "rt")
    else:
        # pylint: disable=consider-using-with
        in_file = open(args.input, "rt")

    if args.output == "-":
        out_file = sys.stdout
    elif args.output.endswith(".gz"):
        # pylint: disable=consider-using-with
        out_file = gzip.open(args.output, "wt")
    else:
        # pylint: disable=consider-using-with
        out_file = open(args.output, "wt")

    hcs = in_file.readline().strip("\r\n").split(args.input_separator)
    record_to_annotable = build_record_to_annotatable(
        vars(args), set(hcs), context=context)
    print(*(hcs + annotation_attributes),
          sep=args.output_separator, file=out_file)

    with pipeline.open() as pipeline:

        for lnum, line in enumerate(in_file):
            try:
                columns = line.strip("\n\r").split(args.input_separator)
                record = dict(zip(hcs, columns))
                annotabale = record_to_annotable.build(record)
                annotation = pipeline.annotate(annotabale)
                print(*(columns + [
                    str(annotation[attrib])
                    for attrib in annotation_attributes]),
                    sep=args.output_separator, file=out_file)
            except Exception:  # pylint: disable=broad-except
                logger.warning(
                    "unexpected input data format at line %s: %s",
                    lnum, line, exc_info=True)

    if args.input != "-":
        in_file.close()

    if args.output != "-":
        out_file.close()


if __name__ == "__main__":
    cli(sys.argv[1:])
