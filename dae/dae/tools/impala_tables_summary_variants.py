#!/usr/bin/env python
import sys
import argparse
import logging
import time
import itertools

from contextlib import closing

from dae.utils.regions import Region

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.backends.impala.impala_variants import ImpalaVariants


logger = logging.getLogger("impala_tables_summary_variants")


def parse_cli_arguments(argv, gpf_instance):
    parser = argparse.ArgumentParser(
        description="loading study parquet files in impala db",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('--verbose', '-V', action='count', default=0)

    parser.add_argument(
        "--studies",
        type=str,
        metavar="<studies IDs>",
        help="comma separated list of study IDs",
    )

    argv = parser.parse_args(argv)
    return argv


def variants_parition_bins(study_backend, partition):
    impala = study_backend._impala_helpers

    partition_bins = []
    with closing(impala.connection()) as connection:
        with connection.cursor() as cursor:
            q = f"SELECT DISTINCT({partition}) FROM " \
                f"{study_backend.db}.{study_backend.variants_table}"
            print(q)
            cursor.execute(q)
            for row in cursor:
                partition_bins.append(row[0])
    print(partition_bins)
    return partition_bins


def collect_summary_schema(impala_variants):
    FAMILY_FIELDS = set([
        "family_index",
        "family_id",
        "variant_in_sexes",
        "variant_in_roles",
        "inheritance_in_members",
        "variant_in_members",
        "family_bin",
        "extra_attributes",
    ])

    schema = {}
    for field_name in impala_variants.schema.col_names:
        if field_name in FAMILY_FIELDS:
            continue
        field_type = impala_variants.schema[field_name]
        schema[field_name] = field_type.type_name

    schema["seen_in_status"] = "tinyint"
    schema["seen_as_denovo"] = "boolean"
    schema["family_variants_count"] = "int"

    return schema


def build_summary_table_name(study_id, impala_variants):
    return f"{impala_variants.db}.{study_id.lower()}_summary_variants "    


PARTITIONS = set([
    "region_bin",
    "frequency_bin",
    "coding_bin",
    "family_bin",
])


def drop_summary_table(study_id, impala_variants):
    impala = impala_variants._impala_helpers
    with closing(impala.connection()) as connection:
        with connection.cursor() as cursor:
            q = f"DROP TABLE IF EXISTS " \
                f"{build_summary_table_name(study_id, impala_variants)}"
            logger.info(f"drop summary table: {q}")
            cursor.execute(q)


def create_summary_table(study_id, impala_variants):
    schema = collect_summary_schema(impala_variants)
    partition_bins = []

    schema_statement = []
    partition_statement = []
    for field_name, field_type in schema.items():
        if field_name in PARTITIONS:
            partition_statement.append(f"`{field_name}` {field_type}")
            partition_bins.append(field_name)
        else:
            schema_statement.append(f"`{field_name}` {field_type}")

    schema_statement = ", ".join(schema_statement)
    partition_statement = ", ".join(partition_statement)

    impala = impala_variants._impala_helpers
    with closing(impala.connection()) as connection:
        with connection.cursor() as cursor:

            q = f"CREATE TABLE IF NOT EXISTS " \
                f"{build_summary_table_name(study_id, impala_variants)} " \
                f"({schema_statement}) " \
                f"PARTITIONED BY ({partition_statement}) " \
                f"STORED AS PARQUET"

            logger.info(f"create summary table: {q}")
            cursor.execute(q)

    return partition_bins


VARIANT_ATTRIBUTES = set([
    "chromosome",
    "position",
    "effect_types",
    "effect_gene_symbols",
])

ENUM_ATTRIBUTES = set([
    "variant_type",
    "transmission_type",
])


def insert_summary_variant(table_name, summary_schema, sa):
    summary_values = []
    partition_values = []
    for field_name, field_type in summary_schema.items():
        if field_name in VARIANT_ATTRIBUTES:
            field_value = getattr(sa, field_name)
        else:
            field_value = sa.get_attribute(field_name)
        if field_name in ENUM_ATTRIBUTES:
            print("\t\t", field_name, type(field_value), field_type)
            field_value = field_value.value

        print("\t", field_name, "=", field_value)

        if field_name in PARTITIONS:
            assert field_value is not None, (field_name, field_value)

            if field_type.lower() in set(["string", "binary"]):
                partition_values.append(
                    f'{field_name} = "{field_value}"')
            else:
                partition_values.append(
                    f"{field_name} = {field_value}")
        else:
            if field_value is None:
                summary_values.append("null")
            elif field_name.lower() in set(["variant_data"]):
                # summary_values.append(field_value.decode("utf8"))
                summary_values.append("null")
            elif field_type.lower() in set(["string"]):
                summary_values.append(f'"{field_value}"')
            else:
                summary_values.append(f"{field_value}")

    partition_values = ", ".join(partition_values)
    summary_values = ", ".join(summary_values)
    insert_statement = f"INSERT INTO " \
        f"{table_name} " \
        f"PARTITION ({partition_values}) " \
        f"VALUES ({summary_values})"
    print(insert_statement)
    return insert_statement


def insert_into_summary_table(
        pedigree_table, variants_table, summary_table,
        summary_schema, parition):

    grouping_fields = [
        "bucket_index",
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

    for field_name, field_type in summary_schema.items():
        if field_name in parition:
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

    insert_partition_statement = []
    select_partition_statement = []
    for bin_name, bin_value in parition.items():
        if bin_name == "region_bin":
            insert_partition_statement.append(
                f"`{bin_name}` = '{bin_value}'")
            select_partition_statement.append(
                f"variants.`{bin_name}` = '{bin_value}'")
        else:
            insert_partition_statement.append(
                f"`{bin_name}` = {bin_value}")
            select_partition_statement.append(
                f"variants.`{bin_name}` = {bin_value}")
    insert_partition_statement = ", ".join(insert_partition_statement)
    select_partition_statement = " AND ".join(select_partition_statement)

    q = f"INSERT INTO {summary_table} ( " \
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
        f"variants.allele_index > 0 AND " \
        f"variants.variant_in_members = pedigree.person_id "\
        f"GROUP BY {grouping_statement}"
    return q


def main(argv=sys.argv[1:], gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    argv = parse_cli_arguments(argv, gpf_instance)

    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    logging.getLogger("impala").setLevel(logging.WARNING)

    if argv.studies is None:
        study_ids = [
            gd.study_id
            for gd in gpf_instance.get_all_genotype_data() if not gd.is_group]
    else:
        study_ids = [sid.strip() for sid in argv.studies.split(",")]

    logger.info(f"building summary variants tables for studies: {study_ids}")

    for study_id in study_ids:
        study = gpf_instance.get_genotype_data(study_id)
        assert study.study_id == study_id

        study_backend = study._backend
        if not isinstance(study_backend, ImpalaVariants):
            logger.warning(f"not an impala study: {study_id}; skipping...")
            continue

        if study_backend.variants_table is None:
            logger.warning(
                f"study {study_id} has no variants; skipping...")
            continue

        drop_summary_table(study_id, study_backend)
        partitions = create_summary_table(study_id, study_backend)

        summary_schema = collect_summary_schema(study_backend)
        summary_table = build_summary_table_name(study_id, study_backend)
        pedigree_table = f"{study_backend.db}.{study_backend.pedigree_table}"
        variants_table = f"{study_backend.db}.{study_backend.variants_table}"

        partition_bins = {}
        # {
        #     'region_bin': [
        #         'chr16_0', 'chrX_0', 'chr2_0', 'chr13_0', 'chr19_0',
        #         'chr7_0', 'chr22_0', 'chr20_0', 'chr5_0', 'chr14_0',
        #         'chr15_0', 'chr6_0', 'other_0', 'chr11_0', 'chr18_0',
        #         'chr8_0', 'chr4_0', 'chr1_0', 'chr3_0', 'chr21_0',
        #         'chr9_0', 'chr10_0', 'chr17_0', 'chr12_0'],
        #     'frequency_bin': [1, 3, 2, 0],
        #     'coding_bin': [1, 0]
        # }

        logger.info(
            f"collecting partitions {partitions} from "
            f"variants table {variants_table}")

        for partition in partitions:
            partition_bins[partition] = variants_parition_bins(
                study_backend, partition)

        logger.info(f"variant table partitions: {partition_bins}")

        impala = study_backend._impala_helpers
        started = time.time()

        all_partitions = list(itertools.product(*partition_bins.values()))
        with closing(impala.connection()) as connection:
            with connection.cursor() as cursor:
                for index, partition in enumerate(all_partitions):
                    partition = {
                        key: value
                        for key, value in zip(partition_bins.keys(), partition)
                    }
                    logger.info(
                        f"building summary table for partition: "
                        f"{index}/{len(all_partitions)}; "
                        f"{partition}")

                    q = insert_into_summary_table(
                        pedigree_table, variants_table, summary_table,
                        summary_schema, partition
                    )
                    logger.debug(
                        f"going to run summary query: {q}")
                    part_started = time.time()
                    cursor.execute(q)

                    part_elapsed = time.time() - part_started
                    logger.info(
                        f"processing partition "
                        f"{index}/{len(all_partitions)} "
                        f"took {part_elapsed:.2f} secs; "
                        f"{partition} "
                    )
                    elapsed = time.time() - started
                    logger.info(
                        f"processing partition "
                        f"{index}/{len(all_partitions)}; "
                        f"total time {elapsed:.2f} secs"
                    )



if __name__ == "__main__":

    main(sys.argv[1:])
