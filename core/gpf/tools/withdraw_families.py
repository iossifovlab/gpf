"""CLI tool to withdraw families from a genotype or phenotype study."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import cast

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from gain.utils.verbosity_configuration import VerbosityConfiguration

from gpf.duckdb_storage.duckdb_genotype_storage import DuckDbParquetStorage
from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.pheno.pheno_data import PhenotypeGroup, PhenotypeStudy
from gpf.studies.study import GenotypeDataStudy

logger = logging.getLogger(__name__)


def _rewrite_parquet(
    path: Path,
    family_ids: set[str],
    *,
    dry_run: bool,
    keep_original: bool,
) -> tuple[int, int]:
    """Drop rows for *family_ids* from *path* and write back atomically.

    Returns ``(before, after)`` row counts.
    """
    table = pq.read_table(path)
    before = len(table)

    col = "familyId" if "familyId" in table.schema.names else "family_id"
    match = pa.compute.is_in(table.column(col), pa.array(list(family_ids)))
    filtered = table.filter(pa.compute.invert(match))
    after = len(filtered)

    if not dry_run and before != after:
        tmp = path.with_suffix(".tmp.parquet")
        try:
            pq.write_table(filtered, tmp)
            if keep_original:
                path.replace(path.with_suffix(".parquet.orig"))
            tmp.replace(path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

    return before, after


def _remove_from_genotype_leaf(
    study: GenotypeDataStudy,
    gpf_instance: GPFInstance,
    family_ids: set[str],
    *,
    dry_run: bool,
    keep_original: bool,
) -> None:
    """Remove *family_ids* from a single leaf genotype study."""
    storage_id = study.config.get("genotype_storage", {}).get("id")
    registry = gpf_instance.genotype_storages
    storage = (
        registry.get_genotype_storage(storage_id)
        if storage_id
        else registry.get_default_genotype_storage()
    )

    if not isinstance(storage, DuckDbParquetStorage):
        logger.warning(
            "[%s] storage type %s is not duckdb_parquet; skipping",
            study.study_id, type(storage).__name__,
        )
        return

    study_data_dir = storage.config.base_dir / study.study_id
    dry_tag = " [dry-run]" if dry_run else ""

    # Pedigree
    ped_path = study_data_dir / "pedigree" / "pedigree.parquet"
    if not ped_path.exists():
        logger.error("[%s] pedigree not found: %s", study.study_id, ped_path)
        return

    before, after = _rewrite_parquet(
        ped_path, family_ids, dry_run=dry_run, keep_original=keep_original,
    )
    logger.info(
        "[%s] pedigree: %d → %d rows (%d removed)%s",
        study.study_id, before, after, before - after, dry_tag,
    )

    # Family variants
    family_dir = study_data_dir / "family"
    if not family_dir.exists():
        logger.info(
            "[%s] no family variants directory at %s; skipping",
            study.study_id, family_dir,
        )
        return

    parquet_files = sorted(family_dir.rglob("*.parquet"))
    logger.info(
        "[%s] scanning %d family variant file(s)%s",
        study.study_id, len(parquet_files), dry_tag,
    )

    total_removed = 0
    for pf in parquet_files:
        before, after = _rewrite_parquet(
            pf, family_ids, dry_run=dry_run, keep_original=keep_original,
        )
        removed = before - after
        if removed:
            logger.info(
                "  %s: %d → %d (%d removed)%s",
                pf.relative_to(family_dir), before, after, removed, dry_tag,
            )
        total_removed += removed

    logger.info(
        "[%s] family variants: %d row(s) removed total%s",
        study.study_id, total_removed, dry_tag,
    )


def _remove_genotype(
    study_id: str,
    gpf_instance: GPFInstance,
    family_ids: set[str],
    *,
    dry_run: bool,
    keep_original: bool,
) -> None:
    study = gpf_instance.get_genotype_data(study_id)
    if study.is_group:
        logger.error(
            "study %r is a group; pass a leaf study ID instead",
            study_id,
        )
        sys.exit(1)
    _remove_from_genotype_leaf(
        cast(GenotypeDataStudy, study), gpf_instance, family_ids,
        dry_run=dry_run, keep_original=keep_original,
    )


def _remove_from_pheno_leaf(
    study: PhenotypeStudy,
    family_ids: set[str],
    *,
    dry_run: bool,
) -> None:
    """Remove *family_ids* from a single leaf phenotype study."""
    dbfile = study.db.dbfile
    dry_tag = " [dry-run]" if dry_run else ""
    logger.info("[%s] phenotype DB: %s%s", study.pheno_id, dbfile, dry_tag)

    family_params = ", ".join(f"'{fid}'" for fid in sorted(family_ids))

    # The study keeps an open read-only connection; DuckDB won't allow
    # a second connection with different read_only settings in the same
    # process. Use the study's existing connection for dry-run, and
    # close it before opening the write connection for actual deletion.
    if dry_run:
        conn = study.db.connection
        n_persons = conn.execute(
            f"SELECT COUNT(*) FROM person"  # noqa: S608
            f" WHERE family_id IN ({family_params})",
        ).fetchone()[0]  # type: ignore[index]
        logger.info(
            "[%s] dry-run: would remove %d person(s)",
            study.pheno_id, n_persons,
        )
        for tbl in study.db.instrument_values_tables.values():
            tname = tbl.alias_or_name
            n = conn.execute(
                f"SELECT COUNT(*) FROM {tname}"  # noqa: S608
                f" WHERE person_id IN"
                f" (SELECT person_id FROM person"
                f"  WHERE family_id IN ({family_params}))",
            ).fetchone()[0]  # type: ignore[index]
            if n:
                logger.info(
                    "[%s] dry-run: would remove %d row(s) from %s",
                    study.pheno_id, n, tname,
                )
        return

    study.db.connection.close()
    conn = duckdb.connect(dbfile, read_only=False)
    try:
        person_ids = [
            row[0]
            for row in conn.execute(
                f"SELECT person_id FROM person"  # noqa: S608
                f" WHERE family_id IN ({family_params})",
            ).fetchall()
        ]
        if not person_ids:
            logger.info(
                "[%s] no persons found for the given families",
                study.pheno_id,
            )
            return

        person_params = ", ".join(f"'{pid}'" for pid in person_ids)

        for tbl in study.db.instrument_values_tables.values():
            tname = tbl.alias_or_name
            conn.execute(
                f"DELETE FROM {tname}"  # noqa: S608
                f" WHERE person_id IN ({person_params})",
            )
            logger.info(
                "[%s] cleared instrument table %s", study.pheno_id, tname,
            )

        conn.execute(
            f"DELETE FROM person WHERE family_id IN ({family_params})",  # noqa: S608
        )
        logger.info(
            "[%s] removed %d person(s)", study.pheno_id, len(person_ids),
        )

        conn.execute(
            f"DELETE FROM family WHERE family_id IN ({family_params})",  # noqa: S608
        )
        logger.info("[%s] removed family record(s)", study.pheno_id)

        conn.execute("CHECKPOINT")
    finally:
        conn.close()


def _remove_pheno(
    study_id: str,
    gpf_instance: GPFInstance,
    family_ids: set[str],
    *,
    dry_run: bool,
) -> None:
    pheno = gpf_instance.get_phenotype_data(study_id)
    if isinstance(pheno, PhenotypeGroup):
        logger.error(
            "study %r is a phenotype group; pass a leaf study ID instead",
            study_id,
        )
        sys.exit(1)
    if not isinstance(pheno, PhenotypeStudy):
        logger.error(
            "unexpected phenotype data type %s for %s",
            type(pheno).__name__, study_id,
        )
        sys.exit(1)
    _remove_from_pheno_leaf(pheno, family_ids, dry_run=dry_run)


def main(
    argv: list[str] | None = None,
    *,
    gpf_instance: GPFInstance | None = None,
) -> None:
    """Remove families from a genotype or phenotype study."""
    parser = argparse.ArgumentParser(
        description=(
            "Remove one or more families from a genotype or phenotype study. "
            "For duckdb_parquet genotype studies the pedigree and family "
            "variant Parquet files are rewritten in place. "
            "For phenotype studies the PhenoDb is updated via SQL DELETE."
        ),
    )
    VerbosityConfiguration.set_arguments(parser)
    parser.add_argument(
        "study",
        help=(
            "Study ID to remove families from. "
            "The GPF instance is used to locate the study data."
        ),
    )
    parser.add_argument(
        "families",
        nargs="+",
        metavar="family_id",
        help="One or more family IDs to remove.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Report what would be removed without modifying any files.",
    )
    parser.add_argument(
        "--keep-original",
        action="store_true",
        default=False,
        help=(
            "Rename each original Parquet file to <file>.parquet.orig "
            "before overwriting it. Has no effect with --dry-run."
        ),
    )

    if argv is None:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    # Allow passing a YAML config path — extract the study ID from it.
    study_arg = args.study
    study_path = Path(study_arg)
    if study_path.exists() and study_path.suffix in {".yaml", ".yml"}:
        with study_path.open() as fh:
            raw_config = yaml.safe_load(fh)
        study_id: str = raw_config.get("id") or study_path.stem
        logger.info("resolved study ID from config: %s", study_id)
    else:
        study_id = study_arg

    family_ids: set[str] = set(args.families)
    logger.info(
        "removing %d family/families from study %r: %s%s",
        len(family_ids), study_id, sorted(family_ids),
        " [dry-run]" if args.dry_run else "",
    )

    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    genotype_ids = set(gpf_instance.get_genotype_data_ids())
    pheno_ids = set(gpf_instance.get_phenotype_data_ids())

    if study_id in genotype_ids:
        _remove_genotype(
            study_id, gpf_instance, family_ids,
            dry_run=args.dry_run, keep_original=args.keep_original,
        )
    elif study_id in pheno_ids:
        _remove_pheno(
            study_id, gpf_instance, family_ids, dry_run=args.dry_run,
        )
    else:
        logger.error(
            "study %r not found in the GPF instance "
            "(checked %d genotype and %d phenotype studies)",
            study_id, len(genotype_ids), len(pheno_ids),
        )
        sys.exit(1)
