#!/usr/bin/env python
import sys
import argparse
import logging
import time

from contextlib import closing


from dae.gpf_instance.gpf_instance import GPFInstance
from dae.impala_storage.schema1.impala_variants import ImpalaVariants


logger = logging.getLogger("impala_tables_stats")


def parse_cli_arguments(argv, gpf_instance):
    parser = argparse.ArgumentParser(
        description="loading study parquet files in impala db",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--verbose", "-V", action="count", default=0)

    parser.add_argument(
        "--studies",
        type=str,
        metavar="<studies IDs>",
        help="comma separated list of study IDs",
    )

    argv = parser.parse_args(argv)
    return argv


def variants_region_bins(study_backend):
    impala = study_backend._impala_helpers

    region_bins = []
    with closing(impala.connection()) as connection:
        with connection.cursor() as cursor:
            q = f"SELECT DISTINCT(region_bin) FROM " \
                f"{study_backend.db}.{study_backend.variants_table}"
            print(q)
            cursor.execute(q)
            for row in cursor:
                region_bins.append(row[0])
    print(region_bins)
    return region_bins


def variants_compute_stats(study_backend, region_bin=None):
    impala = study_backend._impala_helpers
    with closing(impala.connection()) as connection:
        with connection.cursor() as cursor:
            if region_bin is not None:
                q = f"COMPUTE INCREMENTAL STATS " \
                    f"{study_backend.db}.{study_backend.variants_table} " \
                    f"PARTITION (region_bin='{region_bin}')"
            else:
                q = f"COMPUTE STATS " \
                    f"{study_backend.db}.{study_backend.variants_table}"
            logger.info(f"compute stats for variants table: {q}")
            cursor.execute(q)


def summary_variants_compute_stats(study_backend, region_bin=None):
    impala = study_backend._impala_helpers
    with closing(impala.connection()) as connection:
        with connection.cursor() as cursor:
            if region_bin is not None:
                q = f"COMPUTE INCREMENTAL STATS " \
                    f"{study_backend.db}." \
                    f"{study_backend.summary_variants_table} " \
                    f"PARTITION (region_bin='{region_bin}')"
            else:
                q = f"COMPUTE STATS " \
                    f"{study_backend.db}." \
                    f"{study_backend.summary_variants_table}"
            logger.info(f"compute stats for variants table: {q}")
            cursor.execute(q)


def pedigree_compute_stats(study_backend):
    impala = study_backend._impala_helpers
    with closing(impala.connection()) as connection:
        with connection.cursor() as cursor:
            q = f"COMPUTE STATS " \
                f"{study_backend.db}.{study_backend.pedigree_table}"
            logger.info(f"compute stats for pedigree table: {q}")
            cursor.execute(q)


def main(argv=sys.argv[1:], gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

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

    logger.info(f"computing table stats for studies: {study_ids}")

    for study_id in study_ids:
        study = gpf_instance.get_genotype_data(study_id)
        assert study.study_id == study_id

        study_backend = study._backend
        if not isinstance(study_backend, ImpalaVariants):
            logger.info(f"not an impala study: {study_id}; skipping...")
            continue

        pedigree_compute_stats(study_backend)
        if study_backend.variants_table is None:
            continue

        if "region_bin" not in study_backend.schema:
            variants_compute_stats(study_backend, region_bin=None)
            if study_backend.has_summary_variants_table:
                summary_variants_compute_stats(study_backend, region_bin=None)
        else:
            assert "region_bin" in study_backend.schema
            region_bins = variants_region_bins(study_backend)
            logger.info(
                f"processing  {len(region_bins)} region bins; {region_bins}")

            for index, region_bin in enumerate(region_bins):
                start = time.time()
                variants_compute_stats(study_backend, region_bin)

                if study_backend.has_summary_variants_table:
                    summary_variants_compute_stats(study_backend, region_bin)

                elapsed = time.time() - start
                logger.info(
                    f"computing stats {index}/{len(region_bins)} "
                    f"for {study_backend.db}.{study_backend.variants_table}; "
                    f"{elapsed:.2f} secs")


if __name__ == "__main__":

    main(sys.argv[1:])
