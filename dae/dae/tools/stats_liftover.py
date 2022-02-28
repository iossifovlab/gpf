#!/usr/bin/env python

import sys
import argparse
import logging
import textwrap
import pandas as pd
import numpy as np

from typing import cast

from collections import defaultdict, Counter

from dae.utils.variant_utils import mat2str
from dae.variants.variant import VariantDetails

from dae.genomic_resources.reference_genome import \
    open_reference_genome_from_resource
from dae.annotation.annotation_factory import \
    build_annotation_pipeline

from dae.annotation.annotatable import VCFAllele

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.backends.dae.loader import DaeTransmittedLoader
from dae.pedigrees.loader import FamiliesLoader


logger = logging.getLogger("stats_liftover")


def parse_cli_arguments():
    parser = argparse.ArgumentParser(
        description="merge liftover stats")

    parser.add_argument('--verbose', '-V', action='count', default=0)

    parser.add_argument(
        "--stats", help="filename to store liftover statistics",
        default=None,
        nargs="+",
    )

    parser.add_argument(
        "-o", "--output", help="output filename prefix",
        default="merged_stats.txt")

    return parser


def save_liftover_stats(target_stats, stats_filename):

    effects = [
        "CNV+",
        "CNV-",
        "tRNA:ANTICODON",
        "all",
        "splice-site",
        "frame-shift",
        "nonsense",
        "no-frame-shift-newStop",
        "noStart",
        "noEnd",
        "missense",
        "no-frame-shift",
        "CDS",
        "synonymous",
        "coding_unknown",
        "regulatory",
        "3'UTR",
        "5'UTR",
        "intron",
        "non-coding",
        "5'UTR-intron",
        "3'UTR-intron",
        "promoter",
        "non-coding-intron",
        "unknown",
        "intergenic",
        "no-mutation",
    ]

    effects = [e for e in effects if e in target_stats.keys()]
    assert len(effects) == len(target_stats.keys()), (
        list(target_stats.keys()), effects)

    with open(stats_filename, "w") as output:
        header = list(["source", *effects])

        output.write("\t".join(header))
        output.write("\n")

        line = list(
            [
                "source",
                *[str(target_stats[e]["source"]) for e in effects]
            ]
        )
        output.write("\t".join(line))
        output.write("\n")

        for target in ["no_liftover", *effects]:
            line = [target]
            for source in effects:
                line.append(str(target_stats[source].get(target, "")))
            output.write("\t".join(line))
            output.write("\n")


def main(argv=sys.argv[1:], gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    parser = parse_cli_arguments()
    argv = parser.parse_args(argv)

    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    print(argv.stats)

    target_stats = defaultdict(Counter)

    for stats_filename in argv.stats:
        df = pd.read_csv(stats_filename, sep="\t")
        for rec in df.to_dict(orient="records"):
            for k in rec.keys():
                if k == "source":
                    continue
                val = rec[k]
                if np.isnan(val):
                    continue
                target_stats[k][rec["source"]] += val

    print(target_stats)
    save_liftover_stats(target_stats, argv.output)

if __name__ == "__main__":
    main(sys.argv[1:])
