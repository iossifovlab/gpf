#!/usr/bin/env python
import time
import argparse
import logging

from dae.gpf_instance.gpf_instance import GPFInstance

logger = logging.getLogger(__name__)


def generate_row(gpf_instance, gene_symbol):
    gene_weights_db = gpf_instance.gene_weights_db
    config = gpf_instance._autism_gene_profile_config
    autism_scores = dict()
    protection_scores = dict()

    for score in config.autism_scores:
        gw = gene_weights_db.get_gene_weight(score)
        value = gw.get_gene_value(gene_symbol)
        autism_scores[score] = value

    for score in config.protection_scores:
        gw = gene_weights_db.get_gene_weight(score)
        value = gw.get_gene_value(gene_symbol)
        protection_scores[score] = value


def main(gpf_instance=None, argv=None):
    description = "Generate autism gene profile statistics tool"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--verbose', '-V', action='count', default=0)

    args = parser.parse_args(argv)
    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    start = time.time()
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    config = gpf_instance._autism_gene_profile_config
    gene_symbols = set()
    for gene_set_name in config.gene_sets:
        gene_set = gpf_instance.gene_sets_db.get_gene_set(
            "main", gene_set_name)
        gene_symbols.union(set(gene_set["syms"]))
    output = []
    for sym in gene_symbols:
        output.append(generate_row(gpf_instance, sym))
    print(output)
    duration = time.time() - start
    print(duration)


if __name__ == "__main__":
    main()
