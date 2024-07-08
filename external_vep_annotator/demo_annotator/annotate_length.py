import argparse
import csv
import sys
from pathlib import Path

from dae.annotation.annotatable import Annotatable


def annotate_length_cli(raw_args: list[str] | None = None):
    """Dummy tool which outputs annotatable length."""
    if raw_args is None:
        raw_args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="Annotate columns",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input", default="-", nargs="?",
        help="the input file")
    parser.add_argument(
        "output", default="-", nargs="?",
        help="the output file")

    args = parser.parse_args(raw_args)

    # pylint: disable=consider-using-with
    infile = sys.stdin if args.input == "-" else \
        Path(args.input).open("r")  # noqa: SIM115
    outfile = sys.stdout if args.output == "-" else \
        Path(args.output).open("w")  # noqa: SIM115

    with infile, outfile:
        reader = csv.reader(infile, delimiter="\t")
        writer = csv.writer(outfile, delimiter="\t")
        for row in reader:
            if len(row) == 0:
                continue
            annotatable = Annotatable.from_string(row[0])
            length = annotatable.pos_end - annotatable.pos
            writer.writerow([*row, length])


if __name__ == "__main__":
    annotate_length_cli(sys.argv[1:])
