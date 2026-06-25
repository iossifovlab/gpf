"""CLI tool to withdraw families from a duckdb_parquet genotype study.

Only the study's pedigree Parquet file is rewritten (via DuckDB), dropping
every row whose family ID is one of the requested families. The family-variant
Parquet files are deliberately left untouched: at query time a family-variant
row whose family is absent from the pedigree is simply skipped, so the
withdrawn families' variants become inaccessible without rewriting the (large)
variant files. Summary-variant frequencies/counts and cached artifacts
(common reports, denovo gene sets, family counts) are NOT recomputed —
regenerate them with the dedicated tools (e.g. ``generate_common_report``)
if needed.

By default the pedigree is backed up first, as an in-place sibling named
``<stem>.<stamp>.<ext>.bak``, e.g. ``pedigree.20260625T143000Z.parquet.bak``.
Pass ``--no-backup`` to skip the backup, or ``--dry-run`` to report the
intended row changes without touching any file. To restore a backup manually,
move it back over the original::

    mv pedigree.20260625T143000Z.parquet.bak pedigree.parquet
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import cast

import duckdb
from gain.utils.verbosity_configuration import VerbosityConfiguration

from gpf.duckdb_storage.duckdb_genotype_storage import DuckDbParquetStorage
from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.studies.study import GenotypeDataStudy
from gpf.tools.withdraw_families_common import (
    backup_path,
    build_arg_parser,
    make_run_stamp,
    require_study_kind,
)

logger = logging.getLogger(__name__)


def _detect_family_column(conn: duckdb.DuckDBPyConnection, path: Path) -> str:
    """Return the family-id column name (``familyId`` vs ``family_id``)."""
    columns = {
        row[0]
        for row in conn.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)", [str(path)],
        ).fetchall()
    }
    return "familyId" if "familyId" in columns else "family_id"


def _rewrite_parquet(
    conn: duckdb.DuckDBPyConnection,
    path: Path,
    family_ids: set[str],
    *,
    dry_run: bool,
    backup: bool,
    stamp: str,
) -> tuple[int, int]:
    """Drop rows for *family_ids* from *path*, rewriting it via DuckDB.

    Returns ``(before, after)`` row counts. A file with no matching rows is
    left byte-unchanged and is not backed up.
    """
    famcol = _detect_family_column(conn, path)
    placeholders = ", ".join("?" for _ in family_ids)
    params = list(family_ids)

    before = conn.execute(
        "SELECT COUNT(*) FROM read_parquet(?)",
        [str(path)],
    ).fetchone()[0]  # type: ignore[index]
    matching = conn.execute(
        f'SELECT COUNT(*) FROM read_parquet(?) '  # noqa: S608
        f'WHERE "{famcol}" IN ({placeholders})',
        [str(path), *params],
    ).fetchone()[0]  # type: ignore[index]
    after = before - matching

    if matching == 0 or dry_run:
        return before, after

    # Terminal non-".parquet" suffix so an orphaned temp from a crash is
    # never mistaken for a real Parquet file by any "*.parquet" scan.
    tmp = path.with_name(path.name + ".withdraw-tmp")
    try:
        conn.execute(
            f'COPY (SELECT * FROM read_parquet(?) '  # noqa: S608
            f'WHERE "{famcol}" NOT IN ({placeholders})) '
            f"TO '{tmp}' "
            f"(FORMAT parquet, ROW_GROUP_SIZE 50000, COMPRESSION zstd)",
            [str(path), *params],
        )
        if backup:
            # Move the original aside, then move the rewrite into place.
            path.replace(backup_path(path, stamp))
            tmp.replace(path)
        else:
            # Single atomic overwrite: no crash window without the original.
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
    backup: bool,
    stamp: str,
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
        logger.error(
            "[%s] storage type %s is not duckdb_parquet; cannot rewrite",
            study.study_id, type(storage).__name__,
        )
        sys.exit(1)

    study_data_dir = storage.config.base_dir / study.study_id
    dry_tag = " [dry-run]" if dry_run else ""

    with duckdb.connect() as conn:
        conn.execute("SET memory_limit = '4G';")
        conn.execute("SET threads = 1;")
        conn.execute(
            f"SET temp_directory = '{study_data_dir}.withdraw.tmp';",
        )

        ped_path = study_data_dir / "pedigree" / "pedigree.parquet"
        if not ped_path.exists():
            logger.error(
                "[%s] pedigree not found: %s", study.study_id, ped_path,
            )
            sys.exit(1)

        before, after = _rewrite_parquet(
            conn, ped_path, family_ids,
            dry_run=dry_run, backup=backup, stamp=stamp,
        )
        logger.info(
            "[%s] pedigree: %d → %d rows (%d removed)%s",
            study.study_id, before, after, before - after, dry_tag,
        )
        logger.info(
            "[%s] family-variant Parquet files left untouched; withdrawn "
            "families become inaccessible at query time%s",
            study.study_id, dry_tag,
        )


def main(
    argv: list[str] | None = None,
    *,
    gpf_instance: GPFInstance | None = None,
) -> None:
    """Remove families from a duckdb_parquet genotype study."""
    parser = build_arg_parser(
        description=(
            "Remove one or more families from a duckdb_parquet genotype "
            "study by rewriting only its pedigree Parquet file (via DuckDB). "
            "The family-variant files are left untouched; withdrawn families "
            "become inaccessible at query time. The pedigree is backed up by "
            "default as a stamped <stem>.<stamp>.<ext>.bak sibling; restore "
            "by moving the backup back over the original. Summary-variant "
            "frequencies and cached reports are not recomputed."
        ),
    )
    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    study_id: str = args.study
    family_ids: set[str] = set(args.families)
    logger.info(
        "removing %d family/families from genotype study %r: %s%s",
        len(family_ids), study_id, sorted(family_ids),
        " [dry-run]" if args.dry_run else "",
    )

    if gpf_instance is None:
        gpf_instance = GPFInstance.build(args.instance)

    require_study_kind(gpf_instance, study_id, kind="genotypes")

    study = gpf_instance.get_genotype_data(study_id)
    if study.is_group:
        logger.error(
            "study %r is a group; pass a leaf study ID instead", study_id,
        )
        sys.exit(1)

    _remove_from_genotype_leaf(
        cast(GenotypeDataStudy, study), gpf_instance, family_ids,
        dry_run=args.dry_run, backup=not args.no_backup,
        stamp=make_run_stamp(),
    )
