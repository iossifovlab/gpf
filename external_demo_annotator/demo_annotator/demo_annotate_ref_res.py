import argparse
import csv
import sys
from pathlib import Path

from dae.annotation.annotatable import Annotatable
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_file,
)


def annotate_genome_cli(raw_args: list[str] | None = None):
    """Dummy tool which outputs genes for an annotatable."""
    if raw_args is None:
        raw_args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="Annotate genes",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input", nargs="?",
        help="the input file",
    )
    parser.add_argument(
        "genome", nargs="?",
        help="Path to genome file",
    )
    parser.add_argument(
        "output", nargs="?",
        help="the output file",
    )
    parser.add_argument(
        "--format", type=str,
        default=None,
        help="Gene models file format",
    )

    args = parser.parse_args(raw_args)

    # pylint: disable=consider-using-with
    infile = sys.stdin if args.input == "-" else \
        Path(args.input).open("r")  # noqa: SIM115
    outfile = sys.stdout if args.output == "-" else \
        Path(args.output).open("w")  # noqa: SIM115

    if args.genome == "-":
        raise ValueError("Reference genome can't be streamed!")

    genome = build_reference_genome_from_file(
        args.genome,
    )
    genome.open()

    with infile, outfile, genome:
        reader = csv.reader(infile, delimiter="\t")
        writer = csv.writer(outfile, delimiter="\t")
        for row in reader:
            if len(row) == 0:
                continue
            annotatable = Annotatable.from_string(row[0])
            sequence = list(genome.fetch(
                annotatable.chrom, annotatable.pos, annotatable.pos_end,
            ))
            writer.writerow([*row, sequence])


if __name__ == "__main__":
    annotate_genome_cli(sys.argv[1:])
