import argparse
import logging
import sys
from collections import defaultdict

import pandas as pd

from dae.genomic_resources.gene_models import (
    GeneModels,
    build_gene_models_from_resource,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.utils.regions import collapse
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger(__name__)


def cli(argv: list[str] | None = None) -> None:
    """Command line tool to create coding length enrichment background."""
    if argv is None:
        argv = sys.argv[1:]
    description = "Command line tool to create coding length enrichment " \
        "background"
    parser = argparse.ArgumentParser(description=description)
    VerbosityConfiguration.set_arguments(parser)

    parser.add_argument(
        "--grr", "--definition", "-g", type=str,
        default=None,
        help="Path to an extra GRR definition file. This GRR will be loaded"
        "in a group alongside the local one.")

    parser.add_argument(
        dest="gene_models",
        type=str,
        help="Specifies the resource ID of gene models to use")

    parser.add_argument(
        "-o", "--output", type=str, default="coding_len_background.tsv",
        help="Output filename to store the create coding length background")

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    grr: GenomicResourceRepo = \
        build_genomic_resource_repository(file_name=args.grr)
    resource = grr.get_resource(args.gene_models)
    gene_models = build_gene_models_from_resource(resource)
    gene_models.load()

    background_df = build_coding_length_background(gene_models)
    background_df.to_csv(args.output, index=False, sep="\t")


def build_coding_length_background(gene_models: GeneModels) -> pd.DataFrame:
    """Build coding length enrichment background data."""
    genes_coding_regions = defaultdict(list)
    for gm in gene_models.transcript_models.values():
        if gm.chrom.endswith("alt") or gm.chrom.endswith("fix"):
            continue
        genes_coding_regions[gm.gene].extend(gm.cds_regions())

    genes_regions = {}
    for gene, regions in genes_coding_regions.items():
        genes_regions[gene] = collapse(regions)

    genes_lengths = {}
    for gene, regions in genes_regions.items():
        gene_len = sum(len(r) for r in regions)
        genes_lengths[gene.upper()] = gene_len

    df = pd.DataFrame.from_records(
        list(genes_lengths.items()), columns=["gene", "gene_weight"])

    return df
