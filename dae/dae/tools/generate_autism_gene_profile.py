#!/usr/bin/env python
import os
import time
import argparse
import logging

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.variants.attributes import Inheritance
from dae.autism_gene_profile.statistic import AGPStatistic
from dae.autism_gene_profile.db import AutismGeneProfileDB

logger = logging.getLogger(__name__)


def generate_agp(gpf_instance, gene_symbol):
    gene_weights_db = gpf_instance.gene_weights_db
    config = gpf_instance._autism_gene_profile_config
    autism_scores = dict()
    protection_scores = dict()

    gene_sets = gpf_instance.gene_sets_db.get_all_gene_sets("main")
    sets_in = []
    for gs in gene_sets:
        if gene_symbol in gs["syms"]:
            sets_in.append(gs["name"])

    for score in config.autism_scores:
        gw = gene_weights_db.get_gene_weight(score)
        value = gw.get_gene_value(gene_symbol)
        autism_scores[score] = value

    for score in config.protection_scores:
        gw = gene_weights_db.get_gene_weight(score)
        value = gw.get_gene_value(gene_symbol)
        protection_scores[score] = value

    variant_counts = dict()

    for dataset_id, filters in config.datasets.items():
        genotype_data = gpf_instance.get_genotype_data(dataset_id)
        current_counts = dict()
        for ps in filters.person_sets:
            person_set_query = (
                ps.collection_name,
                [ps.set_name]
            )
            for effect in filters.effects:
                counts = current_counts.get(ps.set_name)
                if not counts:
                    current_counts[ps.set_name] = dict()
                    counts = current_counts[ps.set_name]
                fvars = genotype_data.query_variants(
                    genes=[gene_symbol],
                    person_set_collection=person_set_query,
                    effect_types=[effect],
                )
                counts[effect] = len(list(fvars))
        variant_counts[dataset_id] = current_counts

    return AGPStatistic(
        gene_symbol, sets_in, protection_scores,
        autism_scores, variant_counts
    )


def main(gpf_instance=None, argv=None):
    description = "Generate autism gene profile statistics tool"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--verbose', '-V', action='count', default=0)
    default_dbfile = os.path.join(os.getenv("DAE_DB_DIR", "./"), "agpdb")
    parser.add_argument("--dbfile", default=default_dbfile)

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
    gene_symbols = config.gene_symbols
    output = []
    for sym in gene_symbols:
        output.append(generate_agp(gpf_instance, sym))
    duration = time.time() - start
    print(duration)

    agpdb = AutismGeneProfileDB(args.dbfile)

    agpdb.clear_all_tables()
    agpdb.populate_data_tables(gpf_instance)
    for agp in output:
        agpdb.insert_agp(agp)


if __name__ == "__main__":
    main()
