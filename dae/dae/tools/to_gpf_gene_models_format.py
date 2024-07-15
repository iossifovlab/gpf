import argparse
import sys

from dae.genomic_resources.gene_models import (
    build_gene_models_from_file,
    save_as_default_gene_models,
)


def main(argv: list[str] | None = None) -> None:
    """Convert gene models to default GPF gene models format."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Convert gene models to default GPF gene models format")

    parser.add_argument(
        "input_gene_models",
        help="input gene models file",
        type=str,
    )
    parser.add_argument(
        "output_gene_models",
        help="output gene models file",
        type=str,
    )
    parser.add_argument(
        "--gm_format",
        help="gene models format (refseq, ccds or knowngene)",
        type=str,
    )
    parser.add_argument(
        "--gm_names",
        help="gene names mapping file [type None for no mapping]",
        default=None,
        type=str,
    )
    parser.add_argument(
        "--chr_names",
        help="chromosome names mapping file",
        type=str,
        default=None,
    )

    args = parser.parse_args(argv)

    gene_models = build_gene_models_from_file(
        args.input_gene_models,
        file_format=args.gm_format,
        gene_mapping_file_name=args.gm_names,
    )
    gene_models.load()
    if args.chr_names is not None:
        gene_models.relabel_chromosomes(args.chr_names)

    save_as_default_gene_models(gene_models, args.output_gene_models)


if __name__ == "__main__":
    main(sys.argv[1:])
