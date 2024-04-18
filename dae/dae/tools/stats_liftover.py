#!/usr/bin/env python

import argparse
import logging
import sys
from collections import Counter, defaultdict
from typing import Any

import numpy as np
import pandas as pd

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("stats_liftover")


def parse_cli_arguments():
    """Create CLI parser."""
    parser = argparse.ArgumentParser(
        description="merge liftover stats")

    VerbosityConfiguration.set_arguments(parser)

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
    """Produce and save liftover statistics."""
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
    assert len(effects) == len(target_stats.keys())

    with open(stats_filename, "w") as output:
        header = list(["source", *effects])

        output.write("\t".join(header))
        output.write("\n")

        line = list(
            [
                "source",
                *[str(target_stats[e]["source"]) for e in effects],
            ],
        )
        output.write("\t".join(line))
        output.write("\n")

        for target in ["no_liftover", *effects]:
            line = [target]
            for source in effects:
                line.append(str(target_stats[source].get(target, "")))
            output.write("\t".join(line))
            output.write("\n")


def main(argv=None, gpf_instance=None):
    """Print collected liftover statistics."""
    if argv is None:
        argv = sys.argv[1:]
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    parser = parse_cli_arguments()
    argv = parser.parse_args(argv)

    VerbosityConfiguration.set(argv)
    print(argv.stats)

    target_stats: dict[str, Any] = defaultdict(Counter)

    for stats_filename in argv.stats:
        df = pd.read_csv(stats_filename, sep="\t")
        for rec in df.to_dict(orient="records"):
            for k in rec.keys():
                if k == "source":
                    continue
                val = rec[k]
                if np.isnan(val):
                    continue
                target_stats[k][rec["source"]] += val  # type: ignore

    print(target_stats)
    save_liftover_stats(target_stats, argv.output)
