#!/usr/bin/env python
import sys
import argparse
import logging
import time
import itertools
import math
from typing import Any, Optional
from contextlib import closing

from dae.utils.regions import Region
from dae.utils.verbosity_configuration import VerbosityConfiguration
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeDataStudy
from impala_storage.schema1.impala_variants import ImpalaVariants


logger = logging.getLogger("impala_tables_summary_variants")


def parse_cli_arguments(
    argv: list[str], _gpf_instance: GPFInstance
) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="loading study parquet files in impala db",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    VerbosityConfiguration.set_argumnets(parser)
    parser.add_argument(
        "--studies",
        type=str,
        metavar="<studies IDs>",
        help="comma separated list of study IDs",
    )
    parser.add_argument(
        "--split-size",
        type=int,
        metavar="<region split size>",
        default=0,
        help="region bin split size in base pairs")

    return parser.parse_args(argv)


def variants_parition_bins(
    study_backend: ImpalaVariants,
    partition: str
) -> list[str]:
    """Return partition bins."""
    # pylint: disable=protected-access
    impala = study_backend._impala_helpers

    partition_bins = []
    with closing(impala.connection()) as connection:
        with closing(connection.cursor()) as cursor:
            query = f"SELECT DISTINCT({partition}) FROM " \
                f"{study_backend.db}.{study_backend.variants_table}"
            logger.info("collecting patitions: %s", query)
            cursor.execute(query)
            for row in cursor.fetchall():
                partition_bins.append(row[0])
    logger.info("partitions found: %s", partition_bins)
    return partition_bins


def collect_summary_schema(impala_variants: ImpalaVariants) -> dict[str, str]:
    """Collect summary schema."""
    assert impala_variants.schema is not None
    family_fields = set([
        "family_index",
        "family_id",
        "variant_in_sexes",
        "variant_in_roles",
        "inheritance_in_members",
        "variant_in_members",
        "family_bin",
        "extra_attributes",
    ])
    type_map: dict[Any, str] = {
        "int": "int",
        "float": "float",
        "str": "string",
        "bytes": "string",
    }
    schema = {}
    for attr_info in impala_variants.schema:
        field_name = attr_info.name
        if field_name in family_fields:
            continue
        field_type = attr_info.type
        schema[field_name] = type_map[field_type]

    schema["seen_in_status"] = "tinyint"
    schema["seen_as_denovo"] = "boolean"
    schema["family_variants_count"] = "int"

    return schema


def summary_table_name(
    study_id: str,
    impala_variants: ImpalaVariants
) -> str:
    return f"{impala_variants.db}.{study_id.lower()}_summary_variants"


def summary_table_name_temp(
    study_id: str,
    impala_variants: ImpalaVariants
) -> str:
    return f"{impala_variants.db}.{study_id.lower()}_temp_summary_variants"


PARTITIONS = set([
    "region_bin",
    "frequency_bin",
    "coding_bin",
    "family_bin",
])


def drop_summary_table(
    study_id: str,
    impala_variants: ImpalaVariants
) -> None:
    """Drop summary table."""
    # pylint: disable=protected-access
    impala = impala_variants._impala_helpers
    with closing(impala.connection()) as connection:
        with closing(connection.cursor()) as cursor:
            query = f"DROP TABLE IF EXISTS " \
                f"{summary_table_name(study_id, impala_variants)}"
            logger.info("drop summary table: %s", query)
            cursor.execute(query)

            query = f"DROP TABLE IF EXISTS " \
                f"{summary_table_name_temp(study_id, impala_variants)}"
            logger.info("drop summary table: %s", query)
            cursor.execute(query)


def rename_summary_table(
    study_id: str,
    impala_variants: ImpalaVariants
) -> None:
    """Rename summary table."""
    # pylint: disable=protected-access
    impala = impala_variants._impala_helpers
    qry = f"ALTER TABLE {summary_table_name_temp(study_id, impala_variants)} " \
        f"RENAME TO {summary_table_name(study_id, impala_variants)}"
    with closing(impala.connection()) as connection:
        with closing(connection.cursor()) as cursor:
            logger.info("drop summary table: %s", qry)
            cursor.execute(qry)


def create_summary_table(
    study_id: str, impala_variants: ImpalaVariants
) -> list[str]:
    """Create summary table."""
    schema = collect_summary_schema(impala_variants)
    partition_bins = []

    schema_parts = []
    partition_parts = []
    for field_name, field_type in schema.items():
        if field_name in PARTITIONS:
            partition_parts.append(f"`{field_name}` {field_type}")
            partition_bins.append(field_name)
        else:
            schema_parts.append(f"`{field_name}` {field_type}")

    schema_statement = ", ".join(schema_parts)
    if not partition_parts:
        partition_statement = ""
    else:
        partition_statement = ", ".join(partition_parts)
        partition_statement = f"PARTITIONED BY ({partition_statement}) "

    # pylint: disable=protected-access
    impala = impala_variants._impala_helpers
    with closing(impala.connection()) as connection:
        with closing(connection.cursor()) as cursor:

            qry = f"CREATE TABLE IF NOT EXISTS " \
                f"{summary_table_name_temp(study_id, impala_variants)} " \
                f"({schema_statement}) " \
                f"{partition_statement}" \
                f"STORED AS PARQUET"

            logger.info("create summary table: %s", qry)
            cursor.execute(qry)

    return partition_bins


class RegionBinsHelper:
    """Encapsulates data related to region bins."""
    # pylint: disable=too-few-public-methods

    def __init__(self, table_properties: dict, genome: ReferenceGenome):
        self.table_properties = table_properties
        self.chromosomes = self.table_properties["chromosomes"]
        self.region_length = self.table_properties["region_length"]
        self.chromosome_lengths = dict(genome.get_all_chrom_lengths())
        self.region_bins: dict[str, Region] = {}

    # pylint: disable=inconsistent-return-statements
    def _build_region_bins(self) -> None:
        if not self.chromosomes or self.region_length == 0:
            return

        for chrom in self.chromosome_lengths:
            target_chrom = chrom
            if target_chrom not in self.chromosomes:
                target_chrom = "other"
            region_bins_count = math.ceil(
                self.chromosome_lengths[chrom]
                / self.region_length
            )
            for region_index in range(region_bins_count):
                region_bin = f"{target_chrom}_{region_index}"
                region_begin = region_index * self.region_length + 1
                region_end = min(
                    (region_index + 1) * self.region_length,
                    self.chromosome_lengths[chrom])
                region = Region(region_bin, region_begin, region_end)
                if region_bin not in self.region_bins:
                    self.region_bins[region_bin] = region
                else:
                    prev_region = self.region_bins[region_bin]
                    assert prev_region.chrom == region_bin
                    assert prev_region.begin == region.begin
                    assert region.end is not None
                    assert prev_region.end is not None
                    region = Region(
                        region_bin, 1, max(region.end, prev_region.end))
                    self.region_bins[region_bin] = region


def insert_into_summary_table(
    pedigree_table: str,
    variants_table: str,
    summary_table: str,
    summary_schema: dict,
    partition: dict,
    region_bins: dict[str, Region],
    region_split: int = 0
) -> list[str]:
    """Insert into a summary table."""
    # pylint: disable=too-many-locals

    grouping_fields = [
        "bucket_index",
        "position",
        "summary_index",
        "allele_index",
        "effect_types",
        "effect_gene_symbols",
        "variant_type",
        "transmission_type",
    ]
    family_summary_fields = [
        "family_variants_count",
        "seen_in_status",
        "seen_as_denovo"
    ]

    other_fields = []

    for field_name, _field_type in summary_schema.items():
        if field_name in partition:
            # handle partition
            pass
        elif field_name in family_summary_fields:
            # handle family summary data
            pass
        elif field_name in grouping_fields:
            # handle grouping field
            pass
        else:
            other_fields.append(field_name)

    grouping_statement = ", ".join([
        f"`{field}`" for field in grouping_fields
    ])
    insert_other_statement = ", ".join([
        f"`{field}`" for field in other_fields
    ])
    select_other_statement = ", ".join([
        f"MIN(variants.`{field}`)" for field in other_fields
    ])
    insert_family_summary_fields = ", ".join([
        f"`{field}`" for field in family_summary_fields
    ])

    insert_partition_parts = []
    select_partition_parts = []
    for bin_name, bin_value in partition.items():
        if bin_name == "region_bin":
            insert_partition_parts.append(
                f"`{bin_name}` = '{bin_value}'")
            select_partition_parts.append(
                f"variants.`{bin_name}` = '{bin_value}'")
        else:
            insert_partition_parts.append(
                f"`{bin_name}` = {bin_value}")
            select_partition_parts.append(
                f"variants.`{bin_name}` = {bin_value}")
    insert_partition_statement = ", ".join(insert_partition_parts)

    region_bin = partition["region_bin"]
    region = region_bins[region_bin]
    select_partition_statement = " AND ".join(select_partition_parts)

    region_statements = []
    if region_split == 0:
        region_statements.append("")
    else:
        assert region.begin is not None
        assert region.end is not None
        for region_begin in range(region.begin, region.end, region_split):
            region_statement = f"variants.`position` >= {region_begin} AND " \
                f"variants.`position` <= {region_begin + region_split} AND"
            region_statements.append(region_statement)

    queries = []
    for region_statement in region_statements:
        qry = f"INSERT INTO {summary_table} ( " \
            f"{grouping_statement}, " \
            f"{insert_other_statement}, " \
            f"{insert_family_summary_fields}) " \
            f"PARTITION ({insert_partition_statement}) "\
            f"SELECT {grouping_statement}, "\
            f"{select_other_statement}, " \
            f"CAST(COUNT(DISTINCT variants.family_id) AS INT), "\
            f"CAST(gpf_bit_or(pedigree.status) AS TINYINT), "\
            f"CAST(gpf_or(BITAND(inheritance_in_members, 4)) AS BOOLEAN) " \
            f"FROM {variants_table} as variants " \
            f"JOIN {pedigree_table} as pedigree " \
            f"WHERE {select_partition_statement} AND " \
            f"{region_statement} " \
            f"variants.allele_index > 0 AND " \
            f"BITAND(134, variants.inheritance_in_members) != 0 AND " \
            f"( BITAND(8, variants.inheritance_in_members) = 0 AND " \
            f"BITAND(32, variants.inheritance_in_members) = 0 ) AND " \
            f"variants.variant_in_members = pedigree.person_id "\
            f"GROUP BY {grouping_statement}"
        queries.append(qry)
    return queries


def main(
    argv: Optional[list[str]] = None,
    gpf_instance: Optional[GPFInstance] = None
) -> None:
    """Entry point for the script."""
    # flake8: noqa: C901
    # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()
    if argv is None:
        argv = sys.argv[1:]

    args = parse_cli_arguments(argv, gpf_instance)

    VerbosityConfiguration.set(args)

    if args.studies is None:
        study_ids = [
            gd.study_id
            for gd in gpf_instance.get_all_genotype_data() if not gd.is_group]
    else:
        study_ids = [sid.strip() for sid in args.studies.split(",")]

    logger.info("building summary variants tables for studies: %s", study_ids)

    for study_id in study_ids:
        study = gpf_instance.get_genotype_data(study_id)
        assert study.study_id == study_id
        assert isinstance(study, GenotypeDataStudy)

        # pylint: disable=protected-access
        study_backend = study._backend
        if not isinstance(study_backend, ImpalaVariants):
            logger.warning("not an impala study: %s; skipping...", study_id)
            continue

        if study_backend.variants_table is None:
            logger.warning(
                "study %s has no variants; skipping...", study_id)
            continue

        drop_summary_table(study_id, study_backend)
        partitions = create_summary_table(study_id, study_backend)

        summary_schema = collect_summary_schema(study_backend)
        summary_table = summary_table_name_temp(study_id, study_backend)
        pedigree_table = f"{study_backend.db}.{study_backend.pedigree_table}"
        variants_table = f"{study_backend.db}.{study_backend.variants_table}"

        partition_bins = {}

        logger.info(
            "collecting partitions %s from "
            "variants table %s", partitions, variants_table)

        for partition_id in partitions:
            partition_bins[partition_id] = variants_parition_bins(
                study_backend, partition_id)

        logger.info("variant table partitions: %s", partition_bins)

        # pylint: disable=protected-access
        impala = study_backend._impala_helpers
        started = time.time()

        region_bin_helpers = RegionBinsHelper(
            study_backend.table_properties,
            gpf_instance.reference_genome
        )
        region_bin_helpers._build_region_bins()

        logger.info(
            "region bins calculated: %s", region_bin_helpers.region_bins)

        assert set(partition_bins["region_bin"]).issubset(
            set(region_bin_helpers.region_bins.keys()))

        all_partitions = list(itertools.product(*partition_bins.values()))

        for index, partition_values in enumerate(all_partitions):
            partition = dict(zip(partition_bins.keys(), partition_values))
            logger.info(
                "building summary table for partition: %d/%d; %s of %s",
                index, len(all_partitions), partition, study_id)

            part_started = time.time()
            for qry in insert_into_summary_table(
                pedigree_table, variants_table, summary_table,
                summary_schema, partition,
                region_bin_helpers.region_bins,
                args.split_size
            ):
                repeat = 10
                while repeat > 0:
                    try:
                        with closing(impala.connection()) as connection:
                            with closing(connection.cursor()) as cursor:
                                logger.debug(
                                    "going to run partition %s summary query: "
                                    "%s", partition, qry)
                                cursor.execute(qry)
                                break
                    except Exception as ex:  # pylint: disable=broad-except
                        logger.exception("error executing %s", qry)
                        time.sleep(6)
                        repeat -= 1
                        if repeat == 0:
                            raise ex

            part_elapsed = time.time() - part_started

            logger.info(
                "processing partition "
                "%d/%d of %s "
                "took %.2f secs; "
                "%s ",
                index, len(all_partitions), study_id, part_elapsed, partition

            )
            elapsed = time.time() - started
            logger.info(
                "processing partition "
                "%d/%d of %s; "
                "total time %.2f secs",
                index, len(all_partitions), study_id, elapsed
            )

        rename_summary_table(study_id, study_backend)


if __name__ == "__main__":

    main(sys.argv[1:])
