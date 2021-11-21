from __future__ import annotations

import sys
import gzip
import argparse
from .context import Context
from .context import add_context_arguments
from .record_to_annotatable import build_record_to_annotatable
from .record_to_annotatable import add_record_to_annotable_arguments


def configure_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Annotate columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('input', default='-', nargs="?",
                        help="the input column file")
    parser.add_argument('pipeline', default="gpf_instance", nargs="?",
                        help="The pipeline definition file. By default, or if "
                        "the value is gpf_instance, the annotation pipeline "
                        "from the configured gpf instance will be used.")
    parser.add_argument('output', default='-', nargs="?",
                        help="the output column file")

    parser.add_argument('-in_sep', '--input-separator', default="\t",
                        help="The column separator in the input")
    parser.add_argument('-out_sep', '--output-separator', default="\t",
                        help="The column separator in the output")
    parser.add_argument("-v", "--verbosity", action="count", default=0,
                        help="increase output verbosity")
    add_context_arguments(parser)
    add_record_to_annotable_arguments(parser)
    return parser


def cli(raw_args: list[str] = None):
    if not raw_args:
        raw_args = sys.argv[1:]

    parser = configure_argument_parser()
    args = parser.parse_args(raw_args)

    context = Context(args)

    pipeline = context.get_pipeline()
    annotation_attributes = pipeline.annotation_schema.names

    if args.input == "-":
        in_file = sys.stdin
    elif args.input.endswith(".gz"):
        in_file = gzip.open(args.input)
    else:
        in_file = open(args.input)

    if args.output == "-":
        out_file = sys.stdout
    elif args.output.endswith(".gz"):
        out_file = gzip.open(args.output, "w")
    else:
        out_file = open(args.output, "wt")

    hcs = in_file.readline().strip("\r\n").split(args.input_separator)
    record_to_annotable = build_record_to_annotatable(vars(args), hcs)
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
