from __future__ import annotations

import sys
import gzip
import argparse
from dae.annotation.context import Context
from dae.annotation.record_to_annotatable import build_record_to_annotatable
from dae.annotation.record_to_annotatable import \
    add_record_to_annotable_arguments
from dae.genomic_resources.cli import VerbosityConfiguration


def configure_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Annotate columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('input', default='-', nargs="?",
                        help="the input column file")
    parser.add_argument('pipeline', default="context", nargs="?",
                        help="The pipeline definition file. By default, or if "
                        "the value is gpf_instance, the annotation pipeline "
                        "from the configured gpf instance will be used.")
    parser.add_argument('output', default='-', nargs="?",
                        help="the output column file")

    parser.add_argument('-in_sep', '--input-separator', default="\t",
                        help="The column separator in the input")
    parser.add_argument('-out_sep', '--output-separator', default="\t",
                        help="The column separator in the output")
    Context.add_context_arguments(parser)
    add_record_to_annotable_arguments(parser)
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
    annotation_attributes = pipeline.annotation_schema.public_fields

    if args.input == "-":
        in_file = sys.stdin
    elif args.input.endswith(".gz"):
        in_file = gzip.open(args.input, "rt")
    else:
        in_file = open(args.input, "rt")

    if args.output == "-":
        out_file = sys.stdout
    elif args.output.endswith(".gz"):
        out_file = gzip.open(args.output, "wt")
    else:
        out_file = open(args.output, "wt")

    hcs = in_file.readline().strip("\r\n").split(args.input_separator)
    record_to_annotable = build_record_to_annotatable(vars(args), set(hcs))
    print(*(hcs + annotation_attributes),
          sep=args.output_separator, file=out_file)

    for line in in_file:
        cs = line.strip("\n\r").split(args.input_separator)
        record = dict(zip(hcs, cs))
        annotabale = record_to_annotable.build(record)
        annotation = pipeline.annotate(annotabale)
        print(*(cs + [str(annotation[attrib])
                      for attrib in annotation_attributes]),
              sep=args.output_separator, file=out_file)

    if args.input != "-":
        in_file.close()

    if args.output != "-":
        out_file.close()


if __name__ == '__main__':
    cli(sys.argv[1:])
