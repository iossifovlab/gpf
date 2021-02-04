#!/usr/bin/env python
import os
import time
import argparse
import logging

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.variants.attributes import Inheritance
from dae.autism_gene_profile.statistic import AGPStatistic
from dae.autism_gene_profile.db import AutismGeneProfileDB
from dae.utils.effect_utils import expand_effect_types

logger = logging.getLogger(__name__)


def generate_agp(gpf_instance, gene_symbol, variants, person_ids):
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
        if gene_symbol in gw.get_genes():
            value = gw.get_gene_value(gene_symbol)
        else:
            value = None
        autism_scores[score] = value

    for score in config.protection_scores:
        gw = gene_weights_db.get_gene_weight(score)
        if gene_symbol in gw.get_genes():
            value = gw.get_gene_value(gene_symbol)
        else:
            value = None
        protection_scores[score] = value

    variant_counts = dict()

    for dataset_id, filters in config.datasets.items():
        current_counts = dict()
        variant_gene_symbols = {
            eg
            for fv in variants["IossifovWE2014"]
            for eg in fv.effect_gene_symbols
        }
        for ps in filters.person_sets:
            person_set = ps.set_name
            for effect in filters.effects:
                counts = current_counts.get(ps.set_name)
                if not counts:
                    current_counts[person_set] = dict()
                    counts = current_counts[person_set]

                if gene_symbol in variant_gene_symbols:
                    counts[effect] = get_variant_count(
                        gene_symbol, person_set, effect,
                        variants, person_ids, dataset_id
                    )
                else:
                    counts[effect] = 0
        variant_counts[dataset_id] = current_counts

    return AGPStatistic(
        gene_symbol, sets_in, protection_scores,
        autism_scores, variant_counts
    )


def get_variant_count(
        gene_symbol, person_set, effect,
        variants, person_ids, dataset_id):
    pids = set(person_ids[dataset_id][person_set])
    ets = set(expand_effect_types(effect))
    return len(list(filter(
        lambda fv:
            len(pids.intersection(fv.variant_in_members))
            and len(ets.intersection(fv.effect_types))
            and gene_symbol in fv.effect_gene_symbols,
        variants[dataset_id]
    )))


def main(gpf_instance=None, argv=None):
    description = "Generate autism gene profile statistics tool"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--verbose', '-V', '-v', action='count', default=0)
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
    gene_sets = gpf_instance.gene_sets_db.get_all_gene_sets("main")
    gene_sets = list(
        filter(lambda gs: gs["name"] in config.gene_sets, gene_sets)
    )
    gene_symbols = set()
    for gs in gene_sets:
        gene_symbols = gene_symbols.union(gs["syms"])
    print(len(gene_symbols))
    variants = dict()
    person_ids = dict()
    for dataset_id, filters in config.datasets.items():
        genotype_data = gpf_instance.get_genotype_data(dataset_id)
        variants[dataset_id] = list(
            genotype_data.query_variants(genes=gene_symbols)
        )
        person_ids[dataset_id] = dict()
        for ps in filters.person_sets:
            person_set_query = (
                ps.collection_name,
                [ps.set_name]
            )
            person_ids[dataset_id][ps.set_name] = \
                genotype_data._transform_person_set_collection_query(
                    person_set_query, None
                )

    output = []
    gene_symbols = list(gene_symbols)
    gs_count = len(gene_symbols)
    for idx, sym in enumerate(gene_symbols, 1):
        output.append(generate_agp(gpf_instance, sym, variants, person_ids))
        if idx % 25 == 0:
            logger.info(f"Generated {idx}/{gs_count} AGP statistics")
    logger.info("Done generating AGP statistics!")
    duration = time.time() - start
    print(duration)

    agpdb = AutismGeneProfileDB(args.dbfile, clear=True)

    agpdb.clear_all_tables()
    agpdb.populate_data_tables(gpf_instance)
    logger.info("Inserting statistics into DB")
    agpdb.insert_agps(output)
    logger.info("Done")


if __name__ == "__main__":
    main()
