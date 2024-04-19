#!/usr/bin/env python
import argparse
import logging
import sys
import time
from contextlib import closing
from typing import Optional

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeDataStudy
from dae.utils.verbosity_configuration import VerbosityConfiguration
from impala_storage.schema1.impala_variants import ImpalaVariants

logger = logging.getLogger("impala_tables_stats")


def parse_cli_arguments(argv: list[str]) -> argparse.Namespace:
    """Construct parser and parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="loading study parquet files in impala db",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    VerbosityConfiguration.set_arguments(parser)

    parser.add_argument(
        "--studies",
        type=str,
        metavar="<studies IDs>",
        help="comma separated list of study IDs",
    )

    return parser.parse_args(argv)


def variants_region_bins(study_backend: ImpalaVariants) -> list[str]:
    """Collect region bins for a study."""
    impala = study_backend._impala_helpers  # pylint: disable=protected-access

    region_bins = []
    with closing(impala.connection()) as connection:
        with closing(connection.cursor()) as cursor:
            query = f"SELECT DISTINCT(region_bin) FROM " \
                f"{study_backend.db}.{study_backend.variants_table}"
            logger.info("running %s", query)
            cursor.execute(query)
            for row in cursor.fetchall():
                region_bins.append(row[0])
    logger.info("collected region bins: %s", region_bins)
    return region_bins


def variants_compute_stats(
    study_backend: ImpalaVariants,
    region_bin: Optional[str] = None,
) -> None:
    """Compute family variants tables statisticsfor specified region."""
    impala = study_backend._impala_helpers  # pylint: disable=protected-access
    with closing(impala.connection()) as connection:
        with closing(connection.cursor()) as cursor:
            if region_bin is not None:
                query = f"COMPUTE INCREMENTAL STATS " \
                    f"{study_backend.db}.{study_backend.variants_table} " \
                    f"PARTITION (region_bin='{region_bin}')"
            else:
                query = f"COMPUTE STATS " \
                    f"{study_backend.db}.{study_backend.variants_table}"
            logger.info("compute stats for variants table: %s", query)
            cursor.execute(query)


def summary_variants_compute_stats(
    study_backend: ImpalaVariants,
    region_bin: Optional[str] = None,
) -> None:
    """Compute summary variants table statistics."""
    impala = study_backend._impala_helpers  # pylint: disable=protected-access
    with closing(impala.connection()) as connection:
        with closing(connection.cursor()) as cursor:
            if region_bin is not None:
                query = f"COMPUTE INCREMENTAL STATS " \
                    f"{study_backend.db}." \
                    f"{study_backend.summary_variants_table} " \
                    f"PARTITION (region_bin='{region_bin}')"
            else:
                query = f"COMPUTE STATS " \
                    f"{study_backend.db}." \
                    f"{study_backend.summary_variants_table}"
            logger.info("compute stats for variants table: %s", query)
            cursor.execute(query)


def pedigree_compute_stats(study_backend: ImpalaVariants) -> None:
    """Compute pedigree table statistics."""
    impala = study_backend._impala_helpers  # pylint: disable=protected-access
    with closing(impala.connection()) as connection:
        with closing(connection.cursor()) as cursor:
            query = f"COMPUTE STATS " \
                f"{study_backend.db}.{study_backend.pedigree_table}"
            logger.info("compute stats for pedigree table: %s", query)
            cursor.execute(query)


def main(
    argv: Optional[list[str]] = None,
    gpf_instance: Optional[GPFInstance] = None,
) -> None:
    """Run CLI for impala_table_stats.py tool."""
    if argv is None:
        argv = sys.argv[1:]
    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    args = parse_cli_arguments(argv)
    VerbosityConfiguration.set(args)

    if args.studies is None:
        study_ids = [
            gd.study_id
            for gd in gpf_instance.get_all_genotype_data() if not gd.is_group]
    else:
        study_ids = [sid.strip() for sid in args.studies.split(",")]

    logger.info("computing table stats for studies: %s", study_ids)

    for study_id in study_ids:
        study = gpf_instance.get_genotype_data(study_id)
        assert study.study_id == study_id
        assert isinstance(study, GenotypeDataStudy)

        study_backend = study._backend  # pylint: disable=protected-access
        if not isinstance(study_backend, ImpalaVariants):
            logger.info("not an impala study: %s; skipping...", study_id)
            continue
        assert study_backend.schema is not None

        pedigree_compute_stats(study_backend)
        if study_backend.variants_table is None:
            continue

        if "region_bin" not in {a.name for a in study_backend.schema}:
            variants_compute_stats(study_backend, region_bin=None)
            if study_backend.has_summary_variants_table:
                summary_variants_compute_stats(study_backend, region_bin=None)
        else:
            assert "region_bin" in {a.name for a in study_backend.schema}
            region_bins = variants_region_bins(study_backend)
            logger.info(
                "processing  %s region bins; %s",
                len(region_bins), region_bins)

            for index, region_bin in enumerate(region_bins):
                start = time.time()
                variants_compute_stats(study_backend, region_bin)

                if study_backend.has_summary_variants_table:
                    summary_variants_compute_stats(study_backend, region_bin)

                elapsed = time.time() - start
                logger.info(
                    "computing stats %s/%s for %s.%s; %0.2fsec",
                    index, len(region_bins),
                    study_backend.db, study_backend.variants_table, elapsed)


if __name__ == "__main__":
    main(sys.argv[1:])
