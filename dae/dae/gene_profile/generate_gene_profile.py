import argparse
import logging
import os
import pathlib
import sys
import time
from collections import defaultdict
from collections.abc import Iterable, Sequence
from itertools import batched
from typing import Any, cast

from box import Box

from dae.effect_annotation.effect import expand_effect_types
from dae.gene_profile.db import GeneProfileDBWriter
from dae.gene_profile.statistic import GPStatistic
from dae.gene_sets.gene_sets_db import GeneSet
from dae.genomic_resources.gene_models.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.person_sets import PSCQuery
from dae.task_graph.cli_tools import (
    TaskGraphCli,
    task_graph_run_with_results,
)
from dae.task_graph.graph import TaskGraph
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
    statistic_effect_types: set[str] | None,
) -> None:
    """Increment count for specific variant."""
    # pylint: disable=invalid-name
    for gs in variant.effect_gene_symbols:
        if gs not in variant_counts:
            continue

        skip = False
        if statistic_effect_types is not None:
            skip = True
            for allele in variant.alt_alleles:
                allele_gene_effects: dict[str, set[str]] = defaultdict(set)
                for eg in allele.effect_genes:
                    if eg.symbol is None or eg.effect is None:
                        continue
                    allele_gene_effects[eg.symbol].add(eg.effect)

                allele_effects = allele_gene_effects[gs]
                if allele_effects.intersection(statistic_effect_types):
                    skip = False
                    break

        if skip:
            continue

        vc = variant_counts[gs]
        vc[person_set][statistic_id].add(variant.fvuid)


RARE_FREQUENCY_THRESHOLD = 1.0


def build_rare_query(
    statistic: Box,
) -> dict[str, Any]:
    """Build rare variant query."""
    assert statistic.get("category") == "rare"

    query: dict[str, Any] = {
        "frequency_filter": [
            ("af_allele_freq", (None, RARE_FREQUENCY_THRESHOLD))],
        "inheritance": [
            ("not denovo and "
                "not possible_denovo and not possible_omission"),
            "any([mendelian,unknown])",
        ],
    }
    if statistic.effects is not None:
        query["effect_types"] = list(
            expand_effect_types(statistic.effects))
    if statistic.variant_types:
        query["variant_type"] = " or ".join(
            allele_type_from_name(
                statistic.variant_types).repr()  # type: ignore
            for t in statistic.variant_types)
    if statistic.roles:
        query["roles"] = " or ".join(
            repr(Role.from_name(r)) for r in statistic.roles)
    else:
        query["roles"] = "(prb or sib or child) and (mom or dad)"

    if statistic.genomic_scores:
        real_attr_query = []
        for score in statistic.genomic_scores:
            score_name = score["name"]
            score_min = score.get("min")
            score_max = score.get("max")
            assert score_min is not None or score_max is not None

            real_attr_query.append(
                (score_name, (score_min, score_max)))
        query["real_attr_filter"] = real_attr_query

    return query


def process_region(
    regions: list[Region] | None,
    gene_symbols: set[str],
    person_ids: dict[str, Any],
    *,
    gpf_config: str | None = None,
    grr_definition: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Process list of regions to collect variant counts."""
    if grr_definition is not None:
        grr = build_genomic_resource_repository(grr_definition)
    else:
        grr = None
    gpf_instance = GPFInstance.build(gpf_config, grr=grr)
    gene_profiles_config = gpf_instance._gene_profile_config  # noqa: SLF001
    assert gene_profiles_config is not None

    query_genes = list(gene_symbols) if len(gene_symbols) <= 20 else None

    variant_counts = _init_variant_counts(gene_profiles_config, gene_symbols)

    for dataset_id, filters in gene_profiles_config.datasets.items():

        has_denovo = any(
            stats.category == "denovo" for stats in filters.statistics)
        has_rare = any(
            stats.category == "rare" for stats in filters.statistics)

        if has_denovo:
            logger.debug("collecting denovo variants for %s", dataset_id)
            genotype_data = gpf_instance.get_genotype_data(dataset_id)
            assert genotype_data is not None, dataset_id

            denovo_variants = \
                genotype_data.query_variants(
                    regions=regions,
                    genes=query_genes,
                    inheritance="denovo",
                )

            logger.debug("done collecting denovo variants for %s", dataset_id)

            logger.debug("collecting denovo variant counts for %s", dataset_id)
            collect_variant_counts(
                variant_counts[dataset_id],
                denovo_variants,
                dataset_id,
                gene_profiles_config,
                person_ids[dataset_id],
                denovo_flag=True,
            )
            logger.debug(
                "done collecting denovo variant counts for %s", dataset_id,
            )

        if has_rare:
            logger.debug("counting rare variants for %s", dataset_id)

            genotype_data = gpf_instance.get_genotype_data(dataset_id)
            assert genotype_data is not None, dataset_id
            for statistic in filters.statistics:
                if statistic.category != "rare":
                    continue
                query_kwargs = build_rare_query(statistic)
                rare_variants = \
                    genotype_data.query_variants(
                        regions=regions,
                        genes=query_genes,
                        **query_kwargs)

                logger.debug(
                    "counting rare variants for dataset %s", dataset_id)
                collect_variant_counts(
                    variant_counts[dataset_id],
                    rare_variants,
                    dataset_id,
                    gene_profiles_config,
                    person_ids[dataset_id],
                    denovo_flag=False,
                )

            logger.debug(
                "done counting rare variants for dataset %s", dataset_id)
    return variant_counts


def count_variant(
    v: FamilyVariant,
    dataset_id: str,
    variant_counts: dict[str, Any],
    gene_profiles_config: Box,
    person_ids: dict[str, Any], *,
    denovo_flag: bool,
) -> None:
    """Count variant."""
    # pylint: disable=invalid-name, too-many-locals, too-many-branches
    filters = gene_profiles_config.datasets[dataset_id]
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

            in_members = pids.intersection(members)

            if not in_members:
                continue

            if statistic.get("genomic_scores"):
                do_count = _check_variant_genomic_scores(v, statistic)
                if not do_count:
                    continue

            if statistic.get("category") == "rare":
                match = False
                for aa in v.alt_alleles:
                    freq = aa.get_attribute("af_allele_freq")

                    if freq is not None and freq <= RARE_FREQUENCY_THRESHOLD:
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

            statistic_effect_types = None
            if statistic.get("effects"):
                statistic_effect_types = set(
                    expand_effect_types(statistic.effects))

            add_variant_count(
                v, variant_counts, ps.set_name, stat_id, statistic_effect_types,
            )


def _check_variant_genomic_scores(
    v: FamilyVariant,
    statistic: Box,
) -> bool:
    do_count = True
    for score in statistic.genomic_scores:

        score_name = score["name"]
        score_min = score.get("min")
        score_max = score.get("max")
        score_values: list[float] = list(
                        filter(None, v.get_attribute(score_name)))

        if not score_values:
            return False
        if score_min is not None and score_max is not None:
            if not any(score_min <= sv <= score_max for sv in score_values):
                return False
        elif score_min is not None:
            if not any(sv >= score_min for sv in score_values):
                return False
        elif score_max is not None:  # noqa: SIM102
            if not any(sv <= score_max for sv in score_values):
                return False
    return do_count


def collect_variant_counts(
    variant_counts: dict[str, Any],
    variants: Iterable[FamilyVariant],
    dataset_id: str,
    gene_profiles_config: Box,
    person_ids: dict[str, Any], *,
    denovo_flag: bool,
) -> None:
    """Collect variant gene counts for a given dataset."""
    started = time.time()
    for idx, v in enumerate(variants, 1):
        if idx % 1000 == 0:
            elapsed = time.time() - started
            logger.debug(
                "%s: counted %s variants from %s in %.2f seconds",
                dataset_id, idx, dataset_id, elapsed,
            )
        count_variant(
            v, dataset_id, variant_counts, gene_profiles_config, person_ids,
            denovo_flag=denovo_flag,
        )


def build_partitions(
    reference_genome: ReferenceGenome,
    gene_models: GeneModels,
    **kwargs: Any,
) -> Sequence[list[Region] | None]:
    """Build partitions for processing."""
    split_by_chromosome = kwargs.get("split_by_chromosome", True)
    if not split_by_chromosome:
        return [None]

    gene_symbols = kwargs.get("gene_symbols")
    if gene_symbols is None:
        all_chromosomes = set(reference_genome.chromosomes)
    else:
        all_chromosomes = set()
        for gene in gene_symbols:
            if gene not in gene_models.gene_models:
                logger.warning(
                    "Gene symbol %s not found in gene models; skipping",
                    gene,
                )
                continue
            gene_chromosomes = {
                tr.chrom for tr in gene_models.gene_models[gene]}
            all_chromosomes = all_chromosomes.union(gene_chromosomes)

        logger.debug(
            "collected chromosomes from gene symbols: %s", all_chromosomes,
        )

    autosomes = [f"chr{i}" for i in range(1, 23)]
    autosomes_x = [*autosomes, "chrX", "X"]
    autosomes_x = [chrom for chrom in autosomes_x if chrom in all_chromosomes]

    partitions = [
        [Region(chrom)]
        for chrom in autosomes_x
        if chrom in all_chromosomes]
    if len(all_chromosomes - set(autosomes_x)) > 0:
        remaining_chromsomes = [
            chrom for chrom in (all_chromosomes - set(autosomes_x))
            if gene_models.has_chromosome(chrom)
        ]
        logger.debug(
            "adding remaining %s chromosomes to partition %s; %s",
            len(remaining_chromsomes), len(partitions), remaining_chromsomes)
        remaining = [
            Region(chrom) for chrom in remaining_chromsomes]
        if remaining:
            partitions.append(remaining)
    return partitions


def _regions_id(regions: list[Region] | None) -> str:
    """Build regions id."""
    if regions is None:
        return "all_regions"
    return "_".join(f"{r}" for r in regions)


def main(
    gpf_instance: GPFInstance | None = None,
    argv: list[str] | None = None,
) -> None:
    """Entry point for the generate GP script."""
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
    parser.add_argument(
        "--split-by-chromosome", "--split", default=True,
        action="store_true", dest="split_by_chromosome",
        help="Split processing by chromosome "
        "(default)")
    parser.add_argument(
        "--no-split-by-chromosome", "--no-split", default=True,
        action="store_false", dest="split_by_chromosome",
        help="Do not split processing by chromosome "
        "(default)")
    TaskGraphCli.add_arguments(
        parser, use_commands=False, task_progress_mode=False,
    )

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    # pylint: disable=protected-access, invalid-name
    gene_profiles_config = gpf_instance._gene_profile_config  # noqa: SLF001

    assert gene_profiles_config is not None, "No GP configuration found."

    if pathlib.Path(args.dbfile).exists() and not args.drop:
        logger.error(
            "gene profiles DB file %s already exists; "
            "use --drop to drop and recreate the table",
            args.dbfile,
        )
        sys.exit(1)

    gpdb = GeneProfileDBWriter(
        gene_profiles_config.to_dict(),
        args.dbfile,
    )
    if args.drop:
        gpdb.drop_gp_table()
        gpdb.create_gp_table()

    collections_gene_sets = _collect_gene_sets(
        gpf_instance, gene_profiles_config)
    gene_symbols = _collect_gene_symbols(
        gpf_instance, collections_gene_sets, **vars(args))

    gs_count = len(gene_symbols)
    logger.debug("collected %d gene symbols", gs_count)

    person_ids = _collect_person_set_collections(
        gpf_instance, gene_profiles_config)

    gene_profiles = _init_gene_profiles(
        gpf_instance, collections_gene_sets, gene_symbols)

    partitions = build_partitions(
        gpf_instance.reference_genome,
        gene_models=gpf_instance.gene_models,
        gene_symbols=gene_symbols,
        **vars(args))

    variant_counts = _calculate_variant_counts(
        gpf_instance,
        gene_profiles_config,
        gene_symbols,
        person_ids,
        partitions,
        **vars(args),
    )

    _populate_gene_profile_statistics(
        gpf_instance,
        gene_profiles_config,
        gene_profiles,
        variant_counts,
    )

    _insert_gene_profiles_into_db(
        gpdb,
        gene_profiles,
    )


_INSERT_GP_BATCH_SIZE = 1000


def _insert_gene_profiles_into_db(
    gpdb: GeneProfileDBWriter,
    gene_profiles: dict[str, GPStatistic],
) -> None:
    started = time.time()
    logger.debug("inserting statistics into DB")
    batches = batched(gene_profiles.values(), _INSERT_GP_BATCH_SIZE)
    total_batches = (
        len(gene_profiles) + _INSERT_GP_BATCH_SIZE - 1) // _INSERT_GP_BATCH_SIZE

    for idx, gene_profiles_batch in enumerate(batches, 1):
        logger.debug("inserting batch %d/%d", idx, total_batches)
        gpdb.insert_gps(gene_profiles_batch)
        elapsed = time.time() - started
        logger.debug(
            "done inserting batch %d/%d, took %.2f seconds",
            idx, total_batches, elapsed)

    elapsed = time.time() - started
    logger.debug("done inserting GPs; took %.2f secs", elapsed)


def _populate_gene_profile_statistics(
    gpf_instance: GPFInstance,
    gene_profiles_config: Box,
    gene_profiles: dict[str, GPStatistic],
    variant_counts: dict[str, Any],
) -> None:
    for dataset_id in gene_profiles_config.datasets:
        logger.debug("populating gene profile statistics for %s", dataset_id)
        filters = gene_profiles_config.datasets[dataset_id]
        for gs, counts in variant_counts[dataset_id].items():
            gp_counts = gene_profiles[gs].variant_counts
            genotype_data = gpf_instance.get_genotype_data(dataset_id)
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

                    count = len(counts.get(set_name, {}).get(stat_id, set()))
                    if children_count > 0:
                        gp_counts[count_col] = count
                        gp_counts[rate_col] = \
                            (count / children_count) * 1000
                    else:
                        gp_counts[count_col] = 0
                        gp_counts[rate_col] = 0
        logger.debug(
            "done populating gene profile statistics for %s", dataset_id)


def _calculate_variant_counts(
    gpf_instance: GPFInstance,
    gene_profiles_config: Box,
    gene_symbols: set[str],
    person_ids: dict[str, Any],
    partitions: Sequence[list[Region] | None],
    **kwargs: Any,
) -> dict[str, Any]:
    variant_counts: dict[str, Any] = _init_variant_counts(
        gene_profiles_config, gene_symbols)
    graph = TaskGraph()
    for regions in partitions:
        grr_definition = gpf_instance.grr.definition \
            if gpf_instance.grr else None

        graph.create_task(
            f"generate_gene_profiles_{_regions_id(regions)}",
            process_region,
            args=(
                regions,
                gene_symbols,
                person_ids,
            ),
            kwargs={
                "gpf_config": str(gpf_instance.dae_config_path),
                "grr_definition": grr_definition,
            },
        )

    with TaskGraphCli.create_executor(**kwargs) as executor:
        for result_or_error in task_graph_run_with_results(graph, executor):
            if isinstance(result_or_error, Exception):
                raise result_or_error
            region_variant_counts = result_or_error

            variant_counts = _merge_variant_counts(
                gene_profiles_config,
                gene_symbols,
                variant_counts,
                region_variant_counts,
            )

    return variant_counts


def _init_variant_counts(
    gene_profiles_config: Box,
    gene_symbols: set[str],
) -> dict[str, Any]:
    variant_counts: dict[str, Any] = {}

    for dataset_id, filters in gene_profiles_config.datasets.items():
        variant_counts[dataset_id] = {}
        for gs in gene_symbols:
            variant_counts[dataset_id][gs] = {}
            for ps in filters.person_sets:
                ps_statistics: dict[str, Any] = {}
                for statistic in filters.statistics:
                    ps_statistics[statistic.id] = set()
                variant_counts[dataset_id][gs][ps.set_name] = ps_statistics
    return variant_counts


def _merge_variant_counts(
    gene_profiles_config: Box,
    gene_symbols: set[str],
    variant_counts1: dict[str, Any],
    variant_counts2: dict[str, Any],
) -> dict[str, Any]:
    merged_counts: dict[str, Any] = {}

    for dataset_id, filters in gene_profiles_config.datasets.items():
        counts1 = variant_counts1[dataset_id]
        counts2 = variant_counts2[dataset_id]
        merged_counts[dataset_id] = {}
        for gs in gene_symbols:
            merged_counts[dataset_id][gs] = {}
            gs_counts1 = counts1.get(gs, {})
            gs_counts2 = counts2.get(gs, {})
            for ps in filters.person_sets:
                ps_statistics: dict[str, Any] = {}
                for statistic in filters.statistics:
                    stats_count1 = gs_counts1.get(
                        ps.set_name, {}).get(statistic.id, set())
                    stats_count2 = gs_counts2.get(
                        ps.set_name, {}).get(statistic.id, set())
                    ps_statistics[statistic.id] = stats_count1 | stats_count2
                merged_counts[dataset_id][gs][ps.set_name] = ps_statistics

    return merged_counts


def _init_gene_profiles(
    gpf_instance: GPFInstance,
    collections_gene_sets: list[tuple[str, GeneSet]],
    gene_symbols: set[str],
) -> dict[str, Any]:
    start = time.time()
    gene_profiles = {}
    gene_symbols = set(gene_symbols)
    gs_count = len(gene_symbols)

    start = time.time()
    for idx, sym in enumerate(gene_symbols, 1):
        gs, gp = generate_gp(
            gpf_instance, sym, collections_gene_sets,
        )
        gene_profiles[gs] = gp
        if idx % 1000 == 0:
            elapsed = time.time() - start
            logger.debug(
                "initializing %d/%d GP statistics %.2f secs",
                idx, gs_count, elapsed)

    return gene_profiles


def _collect_person_set_collections(
    gpf_instance: GPFInstance,
    gene_profiles_config: Box,
) -> dict[str, Any]:
    person_ids: dict[str, Any] = {}
    for dataset_id, filters in gene_profiles_config.datasets.items():
        genotype_data = gpf_instance.get_genotype_data(dataset_id)
        assert genotype_data is not None, dataset_id
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
            children_person_set = set(person_set)

            person_ids[dataset_id][ps.set_name] = children_person_set
    return person_ids


def _collect_gene_sets(
    gpf_instance: GPFInstance,
    gene_profiles_config: Box,
) -> list[tuple[str, GeneSet]]:
    collections_gene_sets = []

    for gs_category in gene_profiles_config.gene_sets:
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
    logger.debug("collected gene sets: %d", len(collections_gene_sets))

    return collections_gene_sets


def _collect_gene_symbols(
    gpf_instance: GPFInstance,
    collections_gene_sets: list[tuple[str, GeneSet]],
    **kwargs: Any,
) -> set[str]:

    gene_symbols: set[str] = set()
    if kwargs.get("genes"):
        gene_symbols = {gs.strip() for gs in kwargs["genes"].split(",")}
    elif kwargs.get("gene_sets_genes"):
        for _, gs in collections_gene_sets:
            gene_symbols = gene_symbols.union(gs["syms"])
    else:
        gene_models = gpf_instance.gene_models
        gene_symbols = set(gene_models.gene_names())
    return gene_symbols
