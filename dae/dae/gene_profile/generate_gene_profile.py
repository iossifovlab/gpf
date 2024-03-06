#!/usr/bin/env python
import os
import time
import argparse
import logging
from typing import Dict, Any, Set, cast, Iterable, Optional
from box import Box

from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.gene.gene_sets_db import GeneSet
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.gene_profile.statistic import GPStatistic
from dae.gene_profile.db import GeneProfileDB
from dae.effect_annotation.effect import expand_effect_types
from dae.variants.attributes import Role
from dae.variants.family_variant import FamilyVariant, FamilyAllele
from dae.variants.variant import allele_type_from_name

logger = logging.getLogger(__file__)


def generate_gp(
    gpf_instance: GPFInstance,
    gene_symbol: str,
    collections_gene_sets: list[tuple[str, GeneSet]]
) -> tuple[str, GPStatistic]:
    """Generate GP."""
    # pylint: disable=protected-access, invalid-name, too-many-locals
    gene_scores_db = gpf_instance.gene_scores_db
    config = gpf_instance._gene_profile_config
    assert config is not None
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
            gene_score = gene_scores_db.get_gene_score(score_desc.resource_id)
            if gene_symbol in gene_score.get_genes(gene_score_name):
                value = gene_score.get_gene_value(gene_score_name, gene_symbol)
            else:
                value = None
            scores[category_name][gene_score_name] = value

    variant_counts: dict[str, Any] = {}

    return gene_symbol, GPStatistic(
        gene_symbol, sets_in,
        scores, variant_counts
    )


def add_variant_count(
    variant: FamilyVariant,
    variant_counts: dict[str, Any],
    person_set: str,
    statistic_id: str,
    effect_types: Optional[set[str]]
) -> None:
    """Increment count for specific variant."""
    # pylint: disable=invalid-name
    for gs in variant.effect_gene_symbols:
        if gs not in variant_counts:
            continue

        skip = False
        if effect_types is not None:
            skip = True
            for allele in variant.alt_alleles:
                allele_gene_effects: dict[str, set[str]] = {}
                for eg in allele.effect_genes:
                    if eg.symbol is None or eg.effect is None:
                        continue

                    if eg.symbol in allele_gene_effects:
                        allele_gene_effects[eg.symbol].add(eg.effect)
                    else:
                        allele_gene_effects[eg.symbol] = {eg.effect}

                allele_effects = allele_gene_effects.get(gs)
                if allele_effects \
                        and allele_effects.intersection(effect_types):
                    skip = False
                    break

        if skip:
            continue

        vc = variant_counts[gs]
        vc[person_set][statistic_id] += 1


def calculate_table_values(
    instance: GPFInstance,
    variant_counts: dict[str, Any],
    dataset_id: str,
    filters: Box
) -> dict[str, Any]:
    """Calculate GP variant counts and return a SQLite update mapping."""
    # pylint: disable=invalid-name
    table_values: dict[str, Any] = {}
    for gs, counts in variant_counts.items():
        table_values[gs] = {}
        genotype_data = instance.get_genotype_data(dataset_id)
        for ps in filters.person_sets:
            psc = genotype_data.get_person_set_collection(
                ps.collection_name
            )
            assert psc is not None
            set_name = ps.set_name
            person_set = psc.person_sets[set_name]

            children_count = person_set.get_children_count()

            for statistic in filters.statistics:
                stat_id = statistic["id"]

                count_col = f"{dataset_id}_{person_set.id}_{stat_id}"
                rate_col = f"{count_col}_rate"

                count = counts[set_name][stat_id]
                if children_count > 0:
                    table_values[gs][count_col] = count
                    table_values[gs][rate_col] = \
                        (count / children_count) * 1000
                else:
                    table_values[gs][count_col] = 0
                    table_values[gs][rate_col] = 0
    return table_values


def count_variant(
    v: FamilyVariant,
    dataset_id: str,
    variant_counts: dict[str, Any],
    config: Box,
    person_ids: dict[str, Any],
    denovo_flag: bool
) -> None:
    """Count variant."""
    # pylint: disable=invalid-name, too-many-locals, too-many-branches
    filters = config.datasets[dataset_id]
    members = set()

    for aa in v.alt_alleles:
        for member in cast(FamilyAllele, aa).variant_in_members:
            if member is not None:
                members.add(member)

    for ps in filters.person_sets:
        pids = set(person_ids[ps.set_name])

        for statistic in filters.statistics:
            if statistic.category == "denovo" and not denovo_flag:
                continue
            if statistic.category == "rare" and denovo_flag:
                continue

            stat_id = statistic.id

            in_members = len(pids.intersection(members)) > 0

            if not in_members:
                continue

            if statistic.get("scores"):
                do_count = True
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
                if not do_count:
                    continue

            if statistic.get("category") == "rare":
                match = False
                for aa in v.alt_alleles:
                    freq = aa.get_attribute("af_allele_freq")

                    if freq is not None and freq <= 1.0:
                        match = True
                if not match:
                    continue

            if statistic.get("variant_types"):
                variant_types = {
                    allele_type_from_name(t)
                    for t in statistic.variant_types
                }
                if not len(variant_types.intersection(v.variant_types)) > 0:
                    continue

            if statistic.get("roles"):
                roles = {
                    Role.from_name(r)
                    for r in statistic.roles
                }
                v_roles = set(
                    cast(FamilyAllele, v.alt_alleles[0]).variant_in_roles
                )
                if not len(v_roles.intersection(roles)) > 0:
                    continue

            ets = None
            if statistic.get("effects"):
                ets = set(expand_effect_types(statistic.effects))

            add_variant_count(
                v, variant_counts, ps.set_name, stat_id, ets
            )


def collect_variant_counts(
    variant_counts: dict[str, Any],
    variants: Iterable[FamilyVariant],
    dataset_id: str,
    config: Box,
    person_ids: dict[str, Any],
    denovo_flag: bool
) -> None:
    """Collect variant gene counts for a given dataset."""
    for idx, v in enumerate(variants, 1):
        if idx % 1000 == 0:
            logger.info(
                "%s: Counted %s variants from %s", dataset_id, idx, dataset_id
            )
        count_variant(
            v, dataset_id, variant_counts, config, person_ids, denovo_flag
        )


def main(
    gpf_instance: Optional[GPFInstance] = None,
    argv: Optional[list[str]] = None
) -> None:
    """Entry point for the generate GP script."""
    # flake8: noqa: C901
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    description = "Generate gene profile statistics tool"
    parser = argparse.ArgumentParser(description=description)
    VerbosityConfiguration.set_arguments(parser)
    default_dbfile = os.path.join(os.getenv("DAE_DB_DIR", "./"), "gpdb")
    parser.add_argument("--dbfile", default=default_dbfile)
    parser.add_argument(
        "--gene-sets-genes",
        action="store_true",
        help="Generate GPs only for genes contained in the config's gene sets"
    )
    parser.add_argument(
        "--genes",
        help="Comma separated list of genes to generate statistics for"
    )
    parser.add_argument("--drop", action="store_true")

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    start = time.time()
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    # pylint: disable=protected-access, invalid-name
    config = gpf_instance._gene_profile_config

    assert config is not None, "No GP configuration found."

    collections_gene_sets = []

    gpdb = GeneProfileDB(
        config.to_dict(),
        args.dbfile,
        clear=True
    )

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
        genotype_data = gpf_instance.get_genotype_data(dataset_id)
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
            assert person_set is not None, person_set_query
            children_person_set = set(person_set) & genotype_data_children

            person_ids[dataset_id][ps.set_name] = children_person_set

        for stat in filters.statistics:
            if stat.category == "denovo":
                has_denovo = True
            elif stat.category == "rare":
                has_rare = True

    gps = {}
    gene_symbols = set(gene_symbols)
    gs_count = len(gene_symbols)
    elapsed = time.time() - start
    logger.info("data collected: %.2f secs", elapsed)

    start = time.time()
    for idx, sym in enumerate(gene_symbols, 1):
        gs, gp = generate_gp(
            gpf_instance, sym, collections_gene_sets
        )
        gps[gs] = gp
        if idx % 1000 == 0:
            elapsed = time.time() - start
            logger.info(
                "Generated %d/%d GP statistics %.2f secs",
                idx, gs_count, elapsed)

    logger.info("Inserting statistics into DB")
    gpdb.insert_gps(gps.values())

    generate_end = time.time()
    elapsed = generate_end - start
    logger.info("Took %.2f secs", elapsed)

    for dataset_id, filters in config.datasets.items():
        variant_counts: dict[str, Any] = {}
        for gs in gene_symbols:
            variant_counts[gs] = {}
            for ps in filters.person_sets:
                ps_statistics: dict[str, Any] = {}
                for statistic in filters.statistics:
                    ps_statistics[statistic.id] = 0
                variant_counts[gs][ps.set_name] = ps_statistics

        if has_denovo:
            logger.info("Collecting denovo variants for %s", dataset_id)
            genotype_data = gpf_instance.get_genotype_data(dataset_id)
            assert genotype_data is not None, dataset_id
            if args.gene_sets_genes or args.genes:
                genes = list(gene_symbols)
            else:
                genes = None

            denovo_variants = \
                genotype_data.query_variants(
                    genes=genes, inheritance="denovo",
                    unique_family_variants=True
                )

            logger.info("Done collecting denovo variants for %s", dataset_id)

            logger.info("Collecting denovo variant counts for %s", dataset_id)
            collect_variant_counts(
                variant_counts,
                denovo_variants,
                dataset_id,
                config,
                person_ids[dataset_id],
                True
            )
            logger.info(
                "Done collecting denovo variant counts for %s", dataset_id
            )

        if has_rare:
            logger.info("Counting rare variants for %s", dataset_id)

            genotype_data = gpf_instance.get_genotype_data(dataset_id)
            assert genotype_data is not None, dataset_id
            if args.gene_sets_genes or args.genes:
                genes = list(gene_symbols)
            else:
                genes = None

            for statistic in filters.statistics:
                if statistic.category == "denovo":
                    continue
                kwargs: dict[str, Any] = {}
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
                    kwargs["real_attr_filter"] = scores

                if statistic.roles:
                    roles = [
                        repr(Role.from_name(statistic.roles))
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

                logger.info(
                    "Counting rare variants for statistic %s", statistic.id
                )
                collect_variant_counts(
                    variant_counts,
                    rare_variants,
                    dataset_id,
                    config,
                    person_ids[dataset_id],
                    False
                )

            logger.info("Done counting rare variants")

        logger.info("Calculating rates for %s", dataset_id)
        table_values = calculate_table_values(
            gpf_instance,
            variant_counts,
            dataset_id,
            filters
        )
        logger.info("Done calculating rates for %s", dataset_id)
        logger.info("Updating GPs for %s", dataset_id)
        gpdb.update_gps_with_values(table_values)
        logger.info("Done updating GPs for %s", dataset_id)

    elapsed = time.time() - generate_end
    logger.info("Took %.2f secs", elapsed)
