#!/usr/bin/env python
import os
import time
import argparse
import logging
from typing import Dict, Any, Set, cast

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.autism_gene_profile.statistic import AGPStatistic
from dae.autism_gene_profile.db import AutismGeneProfileDB
from dae.effect_annotation.effect import expand_effect_types
from dae.variants.attributes import Role
from dae.variants.variant import allele_type_from_name
from dae.studies.study import GenotypeData

logger = logging.getLogger(__file__)


def generate_agp(gpf_instance, gene_symbol, collections_gene_sets):
    """Generate AGP."""
    # pylint: disable=protected-access, invalid-name, too-many-locals
    gene_scores_db = gpf_instance.gene_scores_db
    config = gpf_instance._autism_gene_profile_config
    scores: Dict[str, Any] = {}

    sets_in = []
    for collection_id, gs in collections_gene_sets:
        if gene_symbol in gs["syms"]:
            gs_name = gs["name"]
            sets_in.append(f"{collection_id}_{gs_name}")

    for category in config.genomic_scores:
        category_name = category["category"]
        scores[category_name] = {}
        for score in category["scores"]:
            gene_score_name = score["score_name"]
            score_desc = gene_scores_db.get_score_desc(gene_score_name)
            gs = gene_scores_db.get_gene_score(score_desc.resource_id)
            if gene_symbol in gs.get_genes(gene_score_name):
                value = gs.get_gene_value(gene_score_name, gene_symbol)
            else:
                value = None
            scores[category_name][gene_score_name] = value

    variant_counts = {}

    for dataset_id, filters in config.datasets.items():
        current_counts: Dict[str, Any] = {}
        for ps in filters.person_sets:
            person_set = ps.set_name
            for statistic in filters.statistics:
                counts = current_counts.get(ps.set_name)
                stat_id = statistic["id"]
                if not counts:
                    current_counts[person_set] = {}
                    counts = current_counts[person_set]

                counts[stat_id] = {
                    "variants": set(),
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
    """Return variant count."""
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


def add_variant_count(variant, agps, dataset_id, person_set, statistic_id):
    """No idea. Please Edit."""
    # pylint: disable=invalid-name
    for gs in variant.effect_gene_symbols:
        if gs not in agps:
            continue

        vc = agps[gs].variant_counts
        variants_fvuids = vc[dataset_id][person_set][statistic_id]["variants"]
        variants_fvuids.add(variant.fvuid)

        # v = variant
        # if v.position == 152171343:
        #     print(100*"^")
        #     print(person_set, statistic_id, v)
        #     print(100*"^")


def calculate_rates(instance, agps, config):
    """No idea. Please edit."""
    # pylint: disable=invalid-name
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

                children_count = len(list(person_set.get_children()))

                for statistic in filters.statistics:
                    stat_id = statistic["id"]

                    stat = agp.variant_counts[dataset_id][set_name][stat_id]
                    count = len(stat["variants"])
                    if children_count > 0:
                        stat["count"] = count
                        stat["rate"] = (count / children_count) * 1000
                    else:
                        stat["count"] = 0
                        stat["rate"] = 0
                    # if stat_id == "rare_lgds":
                    #     from pprint import pprint
                    #     print(100*"=")
                    #     print(stat_id)
                    #     print(set_name)

                    #     pprint(sorted(
                    #         list(stat["variants"].values()),
                    #         key=lambda v:
                    #         f"{v.position:030d}:{v.family_id}"))
                    #     print(80*"~")
                    #     pprint(stat["variants"])

                    #     print(100*"=")


def count_variant(v, dataset_id, agps, config, person_ids, denovo_flag):
    """Count variant."""
    # pylint: disable=invalid-name, too-many-locals, too-many-branches
    filters = config.datasets[dataset_id]
    members = set()

    for aa in v.alt_alleles:
        for member in aa.variant_in_members:
            if member is not None:
                members.add(member)

    for ps in filters.person_sets:
        pids = set(person_ids[dataset_id][ps.set_name])

        for statistic in filters.statistics:
            if statistic.category == "denovo" and not denovo_flag:
                continue
            if statistic.category == "rare" and denovo_flag:
                continue

            stat_id = statistic.id
            do_count = True

            in_members = len(pids.intersection(members)) > 0

            do_count = do_count and in_members

            if statistic.get("effects"):
                ets = set(expand_effect_types(statistic.effects))
                in_effect_types = len(ets.intersection(v.effect_types)) > 0
                do_count = do_count and in_effect_types

            if statistic.get("scores"):
                for score in statistic.scores:
                    score_name = score["name"]
                    score_min = score.get("min")
                    score_max = score.get("max")
                    score_value = v.get_attribute(score_name)[0]

                    if score_value is None:
                        do_count = False

                    if score_min:
                        do_count = do_count and score_value >= score_min
                    if score_max:
                        do_count = do_count and score_value <= score_max

            if statistic.get("category") == "rare":
                match = False
                for aa in v.alt_alleles:
                    freq = aa.get_attribute("af_allele_freq")

                    if freq is not None and freq <= 1.0:
                        match = True
                do_count = do_count and match

            if statistic.get("variant_types"):
                variant_types = {
                    allele_type_from_name(t)
                    for t in statistic.variant_types
                }
                do_count = do_count and \
                    (len(variant_types.intersection(v.variant_types)) > 0)

            if statistic.get("roles"):
                roles = {
                    Role.from_name(r)
                    for r in statistic.roles
                }
                v_roles = set(v.alt_alleles[0].variant_in_roles)
                do_count = do_count and \
                    (len(v_roles.intersection(roles)) > 0)

            if do_count:
                add_variant_count(
                    v, agps, dataset_id, ps.set_name, stat_id
                )


def fill_variant_counts(
        variants, dataset_id, agps, config, person_ids, denovo_flag):
    """If you know what this function does please edit."""
    seen = set()

    for idx, v in enumerate(variants, 1):
        if idx % 1000 == 0:
            logger.info(
                "%s: Counted %s variants from %s", dataset_id, idx, dataset_id
            )
        if v.fvuid in seen:
            continue
        count_variant(
            v, dataset_id, agps, config, person_ids, denovo_flag
        )
        seen.add(v.fvuid)


def main(gpf_instance=None, argv=None):
    """Entry point for the generate AGP script."""
    # flake8: noqa: C901
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    description = "Generate autism gene profile statistics tool"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--verbose", "-V", "-v", action="count", default=0)
    default_dbfile = os.path.join(os.getenv("DAE_DB_DIR", "./"), "agpdb")
    parser.add_argument("--dbfile", default=default_dbfile)
    parser.add_argument(
        "--gene-sets-genes",
        action="store_true",
        help="Generate AGPs only for genes contained in the config's gene sets"
    )
    parser.add_argument(
        "--genes",
        help="Comma separated list of genes to generate statistics for"
    )
    parser.add_argument("--drop", action="store_true")

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
        gpf_instance = GPFInstance.build()

    # pylint: disable=protected-access, invalid-name
    config = gpf_instance._autism_gene_profile_config
    collections_gene_sets = []

    for gs_category in config.gene_sets:
        for gs in gs_category.sets:
            gs_id = gs["set_id"]
            collection_id = gs["collection_id"]
            gene_set = gpf_instance.gene_sets_db.get_gene_set(
                collection_id, gs_id)
            if gene_set is None:
                logger.error("missing gene set: %s, %s", collection_id, gs_id)
                raise ValueError(
                    f"missing gene set: {collection_id}: {gs_id}")

            collections_gene_sets.append((collection_id, gene_set))

    logger.info("collected gene sets: %d", len(collections_gene_sets))

    gene_symbols: Set[str] = set()
    if args.genes:
        gene_symbols = set(gs.strip() for gs in args.genes.split(","))
    elif args.gene_sets_genes:
        for _, gs in collections_gene_sets:
            gene_symbols = gene_symbols.union(gs["syms"])
    else:
        gene_models = gpf_instance.gene_models
        gene_symbols = set(gene_models.gene_names())
    gs_count = len(gene_symbols)
    logger.info("Collected %d gene symbols", gs_count)

    has_denovo = False
    has_rare = False
    person_ids: Dict[str, Any] = {}
    for dataset_id, filters in config.datasets.items():
        genotype_data = cast(
            GenotypeData, gpf_instance.get_genotype_data(dataset_id))
        assert genotype_data is not None
        genotype_data_children = {
            p.person_id
            for p in genotype_data.families.persons_with_parents()
        }
        assert genotype_data is not None, dataset_id
        person_ids[dataset_id] = {}
        for ps in filters.person_sets:
            person_set_query = (
                ps.collection_name,
                [ps.set_name]
            )
            person_set = \
                genotype_data._transform_person_set_collection_query(
                    person_set_query, None
                )
            children_person_set = set(person_set) & genotype_data_children

            person_ids[dataset_id][ps.set_name] = children_person_set

        for stat in filters.statistics:
            if stat.category == "denovo":
                has_denovo = True
            elif stat.category == "rare":
                has_rare = True

    agps = {}
    gene_symbols = set(gene_symbols)
    gs_count = len(gene_symbols)
    elapsed = time.time() - start
    logger.info("data collected: %.2f secs", elapsed)

    start = time.time()
    for idx, sym in enumerate(gene_symbols, 1):
        gs, agp = generate_agp(
            gpf_instance, sym, collections_gene_sets
        )
        agps[gs] = agp
        if idx % 1000 == 0:
            elapsed = time.time() - start
            logger.info(
                "Generated %d/%d AGP statistics %.2f secs",
                idx, gs_count, elapsed)

    logger.info("Done generating AGP statistics!")
    generate_end = time.time()
    elapsed = generate_end - start
    logger.info("Took %.2f secs", elapsed)

    if has_denovo:
        logger.info("Collecting denovo variants")
        # denovo_variants = dict()
        for dataset_id, filters in config.datasets.items():
            genotype_data = gpf_instance.get_genotype_data(dataset_id)
            assert genotype_data is not None, dataset_id
            if args.gene_sets_genes or args.genes:
                genes = gene_symbols
            else:
                genes = None

            denovo_variants = \
                genotype_data.query_variants(genes=genes, inheritance="denovo")

            fill_variant_counts(
                denovo_variants, dataset_id, agps, config, person_ids, True)

        logger.info("Done collecting denovo variants")
        logger.info("Counting denovo variants...")
        logger.info("Done counting denovo variants")

    if has_rare:
        logger.info("Counting rare variants")

        for dataset_id, filters in config.datasets.items():
            genotype_data = gpf_instance.get_genotype_data(dataset_id)
            assert genotype_data is not None, dataset_id
            if args.gene_sets_genes or args.genes:
                genes = gene_symbols
            else:
                genes = None

            for statistic in filters.statistics:
                if statistic.category == "denovo":
                    continue
                kwargs = {}
                kwargs["roles"] = "prb or sib or child"

                if statistic.effects is not None:
                    kwargs["effect_types"] = \
                        expand_effect_types(statistic.effects)

                if statistic.variant_types:
                    variant_types = [
                        # pylint: disable=no-member
                        allele_type_from_name(
                            statistic.variant_types).repr()  # type: ignore
                    ]
                    kwargs["variant_type"] = " or ".join(variant_types)

                if statistic.scores:
                    scores = []
                    for score in statistic.scores:
                        min_max = (score.min, score.max)
                        score_filter = (score.name, min_max)
                        scores.append(score_filter)
                    kwargs["real_attr_filter"] = scores  # type: ignore

                if statistic.roles:
                    roles = [
                        Role.from_name(statistic.roles).repr()
                    ]
                    kwargs["roles"] = " or ".join(roles)

                rare_variants = \
                    genotype_data.query_variants(
                        genes=genes,
                        inheritance=[
                            "not denovo and "
                            "not possible_denovo and not possible_omission",
                            "mendelian or missing"
                        ],
                        frequency_filter=[("af_allele_freq", (None, 1.0))],
                        **kwargs)

                fill_variant_counts(
                    rare_variants, dataset_id, agps, config, person_ids, False)

        logger.info("Done counting rare variants")

    logger.info("Calculating rates...")
    calculate_rates(gpf_instance, agps, config)
    logger.info("Done calculating rates")
    elapsed = time.time() - generate_end
    logger.info("Took %.2f secs", elapsed)

    agpdb = AutismGeneProfileDB(
        gpf_instance._autism_gene_profile_config.to_dict(),
        args.dbfile,
        clear=True
    )

    logger.info("Inserting statistics into DB")
    agpdb.insert_agps(agps.values())
    logger.info("Done")
