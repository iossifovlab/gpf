import argparse
import logging
import os
import time
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from itertools import batched
from typing import Any, cast

from box import Box

from dae.effect_annotation.effect import expand_effect_types
from dae.gene_profile.db import GeneProfileDBWriter
from dae.gene_profile.statistic import GPStatistic
from dae.gene_sets.gene_sets_db import GeneSet
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.person_sets import PSCQuery
from dae.utils.regions import Region
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.variants.attributes import Role
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.variants.variant import allele_type_from_name

logger = logging.getLogger("generate_gene_profile")


def generate_gp(
    gpf_instance: GPFInstance,
    gene_symbol: str,
    collections_gene_sets: list[tuple[str, GeneSet]],
) -> tuple[str, GPStatistic]:
    """Generate GP."""
    # pylint: disable=protected-access, invalid-name, too-many-locals
    gene_scores_db = gpf_instance.gene_scores_db
    config = gpf_instance._gene_profile_config  # noqa: SLF001
    assert config is not None
    scores: dict[str, Any] = {}

    sets_in = []
    for collection_id, gs in collections_gene_sets:
        if gene_symbol in gs["syms"]:
            gs_name = gs["name"]
            sets_in.append(f"{collection_id}_{gs_name}")

    for category in config.gene_scores:
        category_name = category["category"]
        scores[category_name] = {}
        for score in category["scores"]:
            gene_score_name = score["score_name"]
            score_desc = gene_scores_db.get_score_desc(gene_score_name)
            gene_score = gene_scores_db.get_gene_score(score_desc.resource_id)
            value = gene_score.get_gene_value(gene_score_name, gene_symbol)
            scores[category_name][gene_score_name] = value

    variant_counts: dict[str, Any] = {}
    for dataset_id, value in config["datasets"].items():
        statistics = value["statistics"]
        person_sets = value["person_sets"]
        for person_set in person_sets:
            for statistic in statistics:
                col = f'{dataset_id}_{person_set["set_name"]}_{statistic["id"]}'
                col_rate = f"{col}_rate"
                variant_counts[col] = 0
                variant_counts[col_rate] = 0

    return gene_symbol, GPStatistic(
        gene_symbol, sets_in,
        scores, variant_counts,
    )


def add_variant_count(
    variant: FamilyVariant,
    variant_counts: dict[str, Any],
    person_set: str,
    statistic_id: str,
    effect_types: set[str] | None,
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
    gene_profiles: dict[str, GPStatistic],
    dataset_id: str,
    filters: Box,
) -> None:
    """Calculate GP variant counts and return a SQLite update mapping."""
    # pylint: disable=invalid-name
    for gs, counts in variant_counts.items():
        gp_counts = gene_profiles[gs].variant_counts
        genotype_data = instance.get_genotype_data(dataset_id)
        for ps in filters.person_sets:
            psc = genotype_data.get_person_set_collection(
                ps.collection_name,
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
                    gp_counts[count_col] = count
                    gp_counts[rate_col] = \
                        (count / children_count) * 1000
                else:
                    gp_counts[count_col] = 0
                    gp_counts[rate_col] = 0


def process_region(
    regions: list[Region] | None,
    gene_symbols: set[str],
    person_ids: dict[str, Any],
    genes: list[str] | None,
    *,
    has_denovo: bool = False,
    has_rare: bool = False,
    gpf_config: str | None = None,
    grr_definition: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Process list of regions to collect variant counts."""
    if grr_definition is not None:
        grr = build_genomic_resource_repository(grr_definition)
    else:
        grr = None
    gpf_instance = GPFInstance.build(gpf_config, grr=grr)
    config = gpf_instance._gene_profile_config  # noqa: SLF001
    assert config is not None

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

            denovo_variants = \
                genotype_data.query_variants(
                    regions=regions,
                    genes=genes, inheritance="denovo",
                    unique_family_variants=True,
                )

            logger.info("Done collecting denovo variants for %s", dataset_id)

            logger.info("Collecting denovo variant counts for %s", dataset_id)
            collect_variant_counts(
                variant_counts,
                denovo_variants,
                dataset_id,
                config,
                person_ids[dataset_id],
                denovo_flag=True,
            )
            logger.info(
                "Done collecting denovo variant counts for %s", dataset_id,
            )

        if has_rare:
            logger.info("Counting rare variants for %s", dataset_id)

            genotype_data = gpf_instance.get_genotype_data(dataset_id)
            assert genotype_data is not None, dataset_id

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
                            statistic.variant_types).repr(),  # type: ignore
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
                        repr(Role.from_name(statistic.roles)),
                    ]
                    kwargs["roles"] = " or ".join(roles)

                rare_variants = \
                    genotype_data.query_variants(
                        regions=regions,
                        genes=genes,
                        inheritance=[
                            ("not denovo and "
                             "not possible_denovo and not possible_omission"),
                            "mendelian or missing",
                        ],
                        frequency_filter=[("af_allele_freq", (None, 1.0))],
                        **kwargs)

                logger.info(
                    "Counting rare variants for statistic %s", statistic.id,
                )
                collect_variant_counts(
                    variant_counts,
                    rare_variants,
                    dataset_id,
                    config,
                    person_ids[dataset_id],
                    denovo_flag=False,
                )

            logger.info("Done counting rare variants")
    return variant_counts


def count_variant(
    v: FamilyVariant,
    dataset_id: str,
    variant_counts: dict[str, Any],
    config: Box,
    person_ids: dict[str, Any], *,
    denovo_flag: bool,
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
                    cast(FamilyAllele, v.alt_alleles[0]).variant_in_roles,
                )
                if not len(v_roles.intersection(roles)) > 0:
                    continue

            ets = None
            if statistic.get("effects"):
                ets = set(expand_effect_types(statistic.effects))

            add_variant_count(
                v, variant_counts, ps.set_name, stat_id, ets,
            )


def collect_variant_counts(
    variant_counts: dict[str, Any],
    variants: Iterable[FamilyVariant],
    dataset_id: str,
    config: Box,
    person_ids: dict[str, Any], *,
    denovo_flag: bool,
) -> None:
    """Collect variant gene counts for a given dataset."""
    started = time.time()
    for idx, v in enumerate(variants, 1):
        if idx % 1000 == 0:
            elapsed = time.time() - started
            logger.info(
                "%s: Counted %s variants from %s in %.2f seconds",
                dataset_id, idx, dataset_id, elapsed,
            )
        count_variant(
            v, dataset_id, variant_counts, config, person_ids,
            denovo_flag=denovo_flag,
        )


def build_partitions(gpf_instance: GPFInstance) -> list[list[Region]]:
    """Build partitions for processing."""
    all_chromosomes = set(gpf_instance.reference_genome.chromosomes)
    autosomes = [f"chr{i}" for i in range(1, 23)]
    autosomes_xy = [*autosomes, "chrX", "chrY", "X", "Y"]
    autosomes_xy = [chrom for chrom in autosomes_xy if chrom in all_chromosomes]

    partitions = [
        [Region(chrom)]
        for chrom in autosomes_xy
        if chrom in all_chromosomes]
    if len(all_chromosomes - set(autosomes_xy)) > 0:
        gene_models = gpf_instance.gene_models
        remaining_chromsomes = [
            chrom for chrom in (all_chromosomes - set(autosomes_xy))
            if gene_models.has_chromosome(chrom)
        ]
        logger.info("Adding remaining chromosomes to partitions: %s; %s",
                    len(remaining_chromsomes), remaining_chromsomes)
        remaining = [
            Region(chrom) for chrom in remaining_chromsomes]
        partitions.append(remaining)
    return partitions


def main(
    gpf_instance: GPFInstance | None = None,
    argv: list[str] | None = None,
) -> None:
    """Entry point for the generate GP script."""
    # flake8: noqa: C901
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    description = "Generate gene profile statistics tool"
    parser = argparse.ArgumentParser(description=description)
    VerbosityConfiguration.set_arguments(parser)
    default_dbfile = os.path.join(os.getenv("DAE_DB_DIR", "./"), "gpdb.duckdb")
    parser.add_argument("--dbfile", default=default_dbfile)
    parser.add_argument(
        "--gene-sets-genes",
        action="store_true",
        help="Generate GPs only for genes contained in the config's gene sets",
    )
    parser.add_argument(
        "--genes",
        help="Comma separated list of genes to generate statistics for",
    )
    parser.add_argument("--drop", action="store_true")

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    start = time.time()
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    # pylint: disable=protected-access, invalid-name
    config = gpf_instance._gene_profile_config  # noqa: SLF001

    assert config is not None, "No GP configuration found."

    collections_gene_sets = []

    gpdb = GeneProfileDBWriter(
        config.to_dict(),
        args.dbfile,
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

    gene_symbols: set[str] = set()
    if args.genes:
        gene_symbols = {gs.strip() for gs in args.genes.split(",")}
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
    person_ids: dict[str, Any] = {}
    for dataset_id, filters in config.datasets.items():
        genotype_data = gpf_instance.get_genotype_data(dataset_id)
        assert genotype_data is not None, dataset_id
        genotype_data_children = {
            p.person_id
            for p in genotype_data.families.persons_with_parents()
        }
        assert genotype_data is not None, dataset_id
        person_ids[dataset_id] = {}
        for ps in filters.person_sets:
            psc_query = PSCQuery(
                ps.collection_name,
                {ps.set_name},
            )
            psc = genotype_data.get_person_set_collection(psc_query.psc_id)
            assert psc is not None
            person_set = psc.query_person_ids(psc_query)
            assert person_set is not None, psc_query
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
            gpf_instance, sym, collections_gene_sets,
        )
        gps[gs] = gp
        if idx % 1000 == 0:
            elapsed = time.time() - start
            logger.info(
                "Generated %d/%d GP statistics %.2f secs",
                idx, gs_count, elapsed)

    generate_end = time.time()
    elapsed = generate_end - start
    logger.info("Took %.2f secs", elapsed)

    partitions = build_partitions(gpf_instance)

    genes = list(gene_symbols) if args.gene_sets_genes or args.genes else None

    executor = ProcessPoolExecutor(max_workers=10)

    variant_counts: dict[str, Any] = {}
    for filters in config.datasets.values():
        for gs in gene_symbols:
            variant_counts[gs] = {}
            for ps in filters.person_sets:
                ps_statistics: dict[str, Any] = {}
                for statistic in filters.statistics:
                    ps_statistics[statistic.id] = 0
                variant_counts[gs][ps.set_name] = ps_statistics

    tasks = []
    for regions in partitions:
        grr_definition = gpf_instance.grr.definition \
            if gpf_instance.grr else None
        tasks.append(executor.submit(
            process_region,
            regions,
            gene_symbols, person_ids, genes,
            has_denovo=has_denovo,
            has_rare=has_rare,
            gpf_config=str(gpf_instance.dae_config_path),
            grr_definition=grr_definition,
        ))

    for task in tasks:
        region_variant_counts = task.result()

        if len(variant_counts) == 0:
            variant_counts.update(region_variant_counts)
        else:
            for gene_sym, gene_variant_counts in variant_counts.items():
                for collection_id in gene_variant_counts:
                    gs_counts = gene_variant_counts[collection_id]
                    region_gs_counts = region_variant_counts[
                        gene_sym][collection_id]
                    for ps in gs_counts:
                        gs_counts[ps] += region_gs_counts[ps]

    for dataset_id in config.datasets:
        logger.info("Calculating rates for %s", dataset_id)
        calculate_table_values(
            gpf_instance,
            variant_counts,
            gps,
            dataset_id,
            filters,
        )
        logger.info("Done calculating rates for %s", dataset_id)
    logger.info("Inserting statistics into DB")
    batches = batched(gps.values(), 1000)
    for idx, gene_profiles_batch in enumerate(batches, 1):
        logger.info("Inserting batch %d", idx)
        started = time.time()
        gpdb.insert_gps(gene_profiles_batch)
        elapsed = time.time() - started
        logger.info(
            "Done inserting batch %d, took %.2f seconds", idx, elapsed)
    logger.info("Done inserting GPs for %s", dataset_id)

    elapsed = time.time() - generate_end
    logger.info("Took %.2f secs", elapsed)
