#!/usr/bin/env python
import os
import time
import argparse
import logging

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.autism_gene_profile.statistic import AGPStatistic
from dae.autism_gene_profile.db import AutismGeneProfileDB
from dae.utils.effect_utils import expand_effect_types
from dae.variants.attributes import Role

logger = logging.getLogger(__name__)


def generate_agp(gpf_instance, gene_symbol, variants, collections_gene_sets):
    gene_weights_db = gpf_instance.gene_weights_db
    config = gpf_instance._autism_gene_profile_config
    scores = dict()

    sets_in = []
    for collection_id, gs in collections_gene_sets:
        if gene_symbol in gs["syms"]:
            gs_name = gs["name"]
            sets_in.append(f"{collection_id}_{gs_name}")

    for category in config.genomic_scores:
        category_name = category["category"]
        scores[category_name] = dict()
        for score in category["scores"]:
            score_name = score["score_name"]
            gw = gene_weights_db.get_gene_weight(score["score_name"])
            if gene_symbol in gw.get_genes():
                value = gw.get_gene_value(gene_symbol)
            else:
                value = None
            scores[category_name][score_name] = value

    variant_counts = dict()

    for dataset_id, filters in config.datasets.items():
        current_counts = dict()
        for ps in filters.person_sets:
            person_set = ps.set_name
            for effect in filters.effects:
                counts = current_counts.get(ps.set_name)
                if not counts:
                    current_counts[person_set] = dict()
                    counts = current_counts[person_set]

                counts[effect] = {
                    "count": 0,
                    "rate": 0
                }
        variant_counts[dataset_id] = current_counts

    return gene_symbol, AGPStatistic(
        gene_symbol, sets_in,
        scores, variant_counts
    )


def get_variant_count(
        gene_symbol, person_set, effect,
        variants, person_ids, dataset_id):
    pids = set(person_ids[dataset_id][person_set])
    ets = set(expand_effect_types(effect))

    def filter_variant(fv):
        members = set()
        for aa in fv.alt_alleles:
            for member in aa.variant_in_members:
                if member is not None:
                    members.add(member)
        in_members = len(pids.intersection(members)) > 0
        in_effect_types = len(ets.intersection(fv.effect_types)) > 0
        in_gene_syms = gene_symbol in fv.effect_gene_symbols

        return in_members and in_effect_types and in_gene_syms

    return len(list(filter(
        filter_variant,
        variants[dataset_id]
    )))


def add_variant_count(variant, agps, dataset_id, person_set, effect):
    for gs in variant.effect_gene_symbols:
        if gs not in agps:
            continue

        agps[gs].variant_counts[dataset_id][person_set][effect]["count"] += 1


def calculate_rates(instance, agps, config):
    for gs in agps.keys():
        agp = agps[gs]
        for dataset_id, filters in config.datasets.items():
            genotype_data = instance.get_genotype_data(dataset_id)
            for ps in filters.person_sets:
                psc = genotype_data.get_person_set_collection(
                    ps.collection_name
                )
                set_name = ps.set_name
                person_set = psc.person_sets[set_name]

                children_count = len(list(person_set.get_persons_with_roles(
                    Role.prb, Role.sib
                )))

                for effect in filters.effects:
                    stat = agp.variant_counts[dataset_id][set_name][effect]
                    count = stat["count"]
                    stat["rate"] = (count / children_count) * 1000


def fill_variant_counts(variants_datasets, agps, config, person_ids):
    for dataset_id, variants in variants_datasets.items():
        logger.info(f"Counting variants in {dataset_id}")

        filters = config.datasets[dataset_id]

        variants_count = len(variants)

        for idx, v in enumerate(variants, 1):
            if idx % 25 == 0:
                logger.info(
                    f"Counted {idx}/{variants_count} variants"
                )
            members = set()

            for aa in v.alt_alleles:
                for member in aa.variant_in_members:
                    if member is not None:
                        members.add(member)

            for ps in filters.person_sets:
                pids = set(person_ids[dataset_id][ps.set_name])
                for effect in filters.effects:
                    ets = set(expand_effect_types(effect))
                    in_members = len(pids.intersection(members)) > 0
                    in_effect_types = len(ets.intersection(v.effect_types)) > 0
                    if in_members and in_effect_types:
                        add_variant_count(
                            v, agps, dataset_id, ps.set_name, effect
                        )


def main(gpf_instance=None, argv=None):
    description = "Generate autism gene profile statistics tool"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--verbose', '-V', '-v', action='count', default=0)
    default_dbfile = os.path.join(os.getenv("DAE_DB_DIR", "./"), "agpdb")
    parser.add_argument("--dbfile", default=default_dbfile)
    parser.add_argument(
        "--config-genes",
        action="store_true",
        help="Generate AGPs only for genes contained in the config's gene sets"
    )

    args = parser.parse_args(argv)
    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)
    logging.getLogger("impala").setLevel(logging.WARNING)

    start = time.time()
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    config = gpf_instance._autism_gene_profile_config

    # gpf_instance.gene_sets_db.get_all_gene_sets("main")

    collections_gene_sets = []

    for gs_category in config.gene_sets:
        for gs in gs_category.sets:
            gs_id = gs["set_id"]
            collection_id = gs["collection_id"]

            collections_gene_sets.append(
                (
                    collection_id,
                    gpf_instance.gene_sets_db.get_gene_set(
                        collection_id, gs_id
                    )
                )
            )

    # collections_gene_sets = []
    # for name in config.gene_sets:
    #     gene_set = gpf_instance.gene_sets_db.get_gene_set("main", name)
    #     collections_gene_sets.append(gene_set)
    logger.info(f"collected gene sets: {len(collections_gene_sets)}")

    # gene_sets = list(
    #     filter(lambda gs: gs["name"] in config.gene_sets, gene_sets)
    # )
    gene_symbols = set()
    if args.config_genes:
        for _, gs in collections_gene_sets:
            gene_symbols = gene_symbols.union(gs["syms"])
    else:
        gene_models = gpf_instance.get_genome().get_gene_models().gene_models
        gene_symbols = set(gene_models.keys())
    gs_count = len(gene_symbols)
    logger.info(f"Collected {gs_count} gene symbols")
    variants = dict()
    person_ids = dict()
    for dataset_id, filters in config.datasets.items():
        genotype_data = gpf_instance.get_genotype_data(dataset_id)
        assert genotype_data is not None, dataset_id
        if args.config_genes:
            genes = gene_symbols
        else:
            genes = None

        variants[dataset_id] = list(
            genotype_data.query_variants(
                effect_types=filters.effects, genes=genes,
                inheritance="denovo")
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

    agps = dict()
    gene_symbols = list(gene_symbols)
    gs_count = len(gene_symbols)
    elapsed = time.time() - start
    logger.info(f"data collected: {elapsed:.2f} secs")

    start = time.time()
    for idx, sym in enumerate(gene_symbols, 1):
        gs, agp = generate_agp(
            gpf_instance, sym, variants, collections_gene_sets
        )
        agps[gs] = agp
        if idx % 25 == 0:
            elapsed = time.time() - start
            logger.info(
                f"Generated {idx}/{gs_count} AGP statistics "
                f"{elapsed:.2f} secs")

    logger.info("Done generating AGP statistics!")
    generate_end = time.time()
    elapsed = generate_end - start
    logger.info(f"Took {elapsed:.2f} secs")

    logger.info("Counting variants...")
    fill_variant_counts(variants, agps, config, person_ids)
    logger.info("Done counting variants")
    logger.info("Calculating rates...")
    calculate_rates(gpf_instance, agps, config)
    logger.info("Done calculating rates")
    elapsed = time.time() - generate_end
    logger.info(f"Took {elapsed:.2f} secs")

    agpdb = AutismGeneProfileDB(
        gpf_instance._autism_gene_profile_config.to_dict(),
        args.dbfile,
        clear=True
    )

    agpdb.clear_all_tables()
    agpdb.populate_data_tables(gpf_instance.get_genotype_data_ids())
    logger.info("Inserting statistics into DB")
    agpdb.insert_agps(agps.values())
    logger.info("Building AGP output view")
    agpdb.build_agp_view()
    logger.info("Done")


if __name__ == "__main__":
    main()
