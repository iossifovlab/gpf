import argparse
import csv
import sys
from pathlib import Path

from dae.annotation.annotatable import Annotatable
from dae.genomic_resources.gene_models import build_gene_models_from_file


def annotate_genes_cli(raw_args: list[str] | None = None):
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
        "gene_models", nargs="?",
        help="Path to gene models file",
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

    if args.gene_models == "-":
        raise ValueError("Gene models cannot be streamed!")

    gene_models = build_gene_models_from_file(
        args.gene_models, file_format=args.format,
    )
    gene_models.load()

    with infile, outfile:
        reader = csv.reader(infile, delimiter="\t")
        writer = csv.writer(outfile, delimiter="\t")
        for row in reader:
            if len(row) == 0:
                continue
            annotatable = Annotatable.from_string(row[0])
            gene_syms = {
                tr.gene for tr in
                gene_models.gene_models_by_location(
                    annotatable.chrom,
                    annotatable.pos,
                    annotatable.pos_end,
                )
            }
            writer.writerow([*row, ",".join(gene_syms)])


if __name__ == "__main__":
    annotate_genes_cli(sys.argv[1:])
