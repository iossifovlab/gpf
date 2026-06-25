"""CLI tool to withdraw families from a phenotype study.

The phenotype PhenoDb is updated via SQL ``DELETE`` of every person,
instrument-value row, and family record belonging to the requested families.

By default the database file is backed up first, as an in-place sibling named
``<stem>.<stamp>.<ext>.bak`` (one shared UTC stamp per run), e.g.
``test_pheno.20260625T143000Z.db.bak``. Pass ``--no-backup`` to skip the
backup, or ``--dry-run`` to report the intended row changes without touching
the database. To restore a backup manually, copy it back over the original::

    cp test_pheno.20260625T143000Z.db.bak test_pheno.db
"""
from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

import duckdb
from gain.utils.verbosity_configuration import VerbosityConfiguration

from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.pheno.pheno_data import PhenotypeGroup, PhenotypeStudy
from gpf.tools.withdraw_families_common import (
    backup_path,
    build_arg_parser,
    make_run_stamp,
    require_study_kind,
)

logger = logging.getLogger(__name__)


def _remove_from_pheno_leaf(
    study: PhenotypeStudy,
    family_ids: set[str],
    *,
    dry_run: bool,
    backup: bool,
    stamp: str,
) -> None:
    """Remove *family_ids* from a single leaf phenotype study."""
    dbfile = study.db.dbfile
    dry_tag = " [dry-run]" if dry_run else ""
    logger.info("[%s] phenotype DB: %s%s", study.pheno_id, dbfile, dry_tag)

    # Sort for deterministic logging; the WHERE values themselves go
    # through DuckDB ``?`` placeholders, never string interpolation.
    family_values = sorted(family_ids)
    fam_placeholders = ", ".join(["?"] * len(family_values))

    # The study keeps an open read-only connection; DuckDB won't allow
    # a second connection with different read_only settings in the same
    # process. Use the study's existing connection for dry-run, and
    # close it before opening the write connection for actual deletion.
    if dry_run:
        conn = study.db.connection
        n_persons = conn.execute(
            f"SELECT COUNT(*) FROM person"  # noqa: S608
            f" WHERE family_id IN ({fam_placeholders})",
            family_values,
        ).fetchone()[0]  # type: ignore[index]
        logger.info(
            "[%s] dry-run: would remove %d person(s)",
            study.pheno_id, n_persons,
        )
        for tbl in study.db.instrument_values_tables.values():
            # Table names come from study.db.instrument_values_tables —
            # trusted internal identifiers, not user input. They are
            # identifiers (not values), so they cannot be placeholders.
            tname = tbl.alias_or_name
            n = conn.execute(
                f"SELECT COUNT(*) FROM {tname}"  # noqa: S608
                f" WHERE person_id IN"
                f" (SELECT person_id FROM person"
                f"  WHERE family_id IN ({fam_placeholders}))",
                family_values,
            ).fetchone()[0]  # type: ignore[index]
            if n:
                logger.info(
                    "[%s] dry-run: would remove %d row(s) from %s",
                    study.pheno_id, n, tname,
                )
        return

    study.db.connection.close()
    if backup:
        bak = backup_path(Path(dbfile), stamp)
        shutil.copy2(dbfile, bak)
        logger.info("[%s] original DB backed up as %s", study.pheno_id, bak)
    conn = duckdb.connect(dbfile, read_only=False)
    try:
        person_ids = [
            row[0]
            for row in conn.execute(
                f"SELECT person_id FROM person"  # noqa: S608
                f" WHERE family_id IN ({fam_placeholders})",
                family_values,
            ).fetchall()
        ]
        if not person_ids:
            logger.info(
                "[%s] no persons found for the given families",
                study.pheno_id,
            )
            return

        person_values = sorted(person_ids)
        person_placeholders = ", ".join(["?"] * len(person_values))

        for tbl in study.db.instrument_values_tables.values():
            # Trusted internal table identifier (see dry-run note above);
            # the person_id WHERE values use placeholders.
            tname = tbl.alias_or_name
            conn.execute(
                f"DELETE FROM {tname}"  # noqa: S608
                f" WHERE person_id IN ({person_placeholders})",
                person_values,
            )
            logger.info(
                "[%s] cleared instrument table %s", study.pheno_id, tname,
            )

        conn.execute(
            # f-string only injects "?" placeholders; values are bound.
            f"DELETE FROM person WHERE family_id IN ({fam_placeholders})",  # noqa: S608
            family_values,
        )
        logger.info(
            "[%s] removed %d person(s)", study.pheno_id, len(person_ids),
        )

        conn.execute(
            # f-string only injects "?" placeholders; values are bound.
            f"DELETE FROM family WHERE family_id IN ({fam_placeholders})",  # noqa: S608
            family_values,
        )
        logger.info("[%s] removed family record(s)", study.pheno_id)

        conn.execute("CHECKPOINT")
    finally:
        conn.close()


def main(
    argv: list[str] | None = None,
    *,
    gpf_instance: GPFInstance | None = None,
) -> None:
    """Remove families from a phenotype study."""
    parser = build_arg_parser(
        description=(
            "Remove one or more families from a phenotype study by deleting "
            "their persons, instrument values and family records from the "
            "PhenoDb via SQL DELETE. The database is backed up by default as "
            "a stamped <stem>.<stamp>.<ext>.bak sibling; restore by copying "
            "the backup back over the original."
        ),
    )
    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    study_id: str = args.study
    family_ids: set[str] = set(args.families)
    logger.info(
        "removing %d family/families from phenotype study %r: %s%s",
        len(family_ids), study_id, sorted(family_ids),
        " [dry-run]" if args.dry_run else "",
    )

    if gpf_instance is None:
        gpf_instance = GPFInstance.build(args.instance)

    require_study_kind(gpf_instance, study_id, kind="phenotypes")

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

    _remove_from_pheno_leaf(
        pheno, family_ids,
        dry_run=args.dry_run, backup=not args.no_backup,
        stamp=make_run_stamp(),
    )
