import argparse
import logging
import sys
from collections import Counter
from typing import Optional

import pandas as pd

from dae.gpf_instance import GPFInstance
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("build_ur_synonymous_enrichment_background")


def cli(
    argv: Optional[list[str]] = None,
    gpf_instance: Optional[GPFInstance] = None,
) -> None:
    """Command line tool to create UR synonymous enrichment background."""
    if argv is None:
        argv = sys.argv[1:]
    description = "Command line tool to create UR synonymous enrichment " \
        "background."
    parser = argparse.ArgumentParser(description=description)
    VerbosityConfiguration.set_arguments(parser)

    parser.add_argument(
        dest="study_id",
        type=str,
        help="Specifies the study ID to use for building the background")

    parser.add_argument(
        "--parents-called", type=int, default=600,
        help="Minimal number of parents called")

    parser.add_argument(
        "-o", "--output", type=str, default="ur_synonymous_background.tsv",
        help="Output filename to store the create enrichment background")

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    study = gpf_instance.get_genotype_data(args.study_id)
    if study is None:
        raise ValueError(f"Study '{args.study_id}' not found")
    if study.is_group:
        raise ValueError(f"Study '{args.study_id}' is a group")

    vs = study.query_variants(
        effect_types=["synonymous"],
        inheritance="mendelian or missing",
        ultra_rare=True,
        frequency_filter=[
            ("af_parents_called_count", (args.parents_called, None))],
    )

    affected_genes = []
    for count, v in enumerate(vs):
        for aa in v.alt_alleles:
            assert aa.effects is not None
            allele_gene_set = set()
            for ge in aa.effects.genes:
                if ge.effect == "synonymous":
                    assert ge.symbol is not None
                    allele_gene_set.add(ge.symbol.upper())

            affected_genes.append(allele_gene_set)
        if (count + 1) % 1000 == 0:
            logger.info("Processed %s variants", count + 1)

    gene_counts: dict[str, int] = Counter()

    for allele_gene_set in affected_genes:
        for gene in allele_gene_set:
            gene_counts[gene] += 1

    df = pd.DataFrame.from_records(
        list(gene_counts.items()), columns=["gene", "gene_weight"])
    df.to_csv(args.output, index=False, sep="\t")
