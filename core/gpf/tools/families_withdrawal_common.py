"""Shared helpers for the families-withdrawal CLI tools.

Two purpose-specific tools build on this module:

- ``families_withdrawal_genotypes`` rewrites the pedigree Parquet file of a
  ``duckdb_parquet`` genotype study via DuckDB (the family-variant files are
  left untouched; withdrawn families become inaccessible at query time).
- ``families_withdrawal_phenotypes`` removes families from a phenotype study
  via SQL ``DELETE``.

Both back up every file they modify by default. A backup is an in-place
sibling named ``<stem>.<stamp>.<ext>.bak`` where ``<stamp>`` is a single
UTC timestamp shared across every file modified in one run. To restore a
backup manually, move (or copy) it back over the original, e.g.::

    mv pedigree.20260625T143000Z.parquet.bak pedigree.parquet
    cp test_pheno.20260625T143000Z.db.bak test_pheno.db

The terminal ``.bak`` suffix keeps backups out of the ``*.parquet`` scan,
so a study can be processed repeatedly without re-processing prior backups.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from gain.utils.verbosity_configuration import VerbosityConfiguration

if TYPE_CHECKING:
    from gpf.gpf_instance.gpf_instance import GPFInstance

logger = logging.getLogger(__name__)

_OTHER_TOOL = {
    "genotypes": "families_withdrawal_phenotypes",
    "phenotypes": "families_withdrawal_genotypes",
}


def require_study_kind(
    gpf_instance: GPFInstance,
    study_id: str,
    *,
    kind: Literal["genotypes", "phenotypes"],
) -> None:
    """Validate that *study_id* is of the expected *kind*.

    Exits with code 1 if the study is of the other kind (pointing at the
    matching tool) or if it is unknown to the instance entirely.
    """
    genotype_ids = set(gpf_instance.get_genotype_data_ids())
    pheno_ids = set(gpf_instance.get_phenotype_data_ids())

    wanted = genotype_ids if kind == "genotypes" else pheno_ids
    if study_id in wanted:
        return

    other = pheno_ids if kind == "genotypes" else genotype_ids
    if study_id in other:
        logger.error(
            "study %r is a %s study; use %s instead",
            study_id,
            "phenotype" if kind == "genotypes" else "genotype",
            _OTHER_TOOL[kind],
        )
        sys.exit(1)

    logger.error(
        "study %r not found in the GPF instance "
        "(checked %d genotype and %d phenotype studies)",
        study_id, len(genotype_ids), len(pheno_ids),
    )
    sys.exit(1)


def make_run_stamp() -> str:
    """Return a single UTC stamp for one run, e.g. ``20260625T143000Z``."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def backup_path(path: Path, stamp: str) -> Path:
    """Return the ``<stem>.<stamp>.<ext>.bak`` sibling of *path*.

    ``stem`` is the filename without its final extension and ``ext`` is the
    final suffix (without the leading dot). The terminal ``.bak`` keeps the
    backup out of any ``*.parquet`` glob scan.
    """
    ext = path.suffix.lstrip(".")
    stem = path.name[: -len(path.suffix)] if path.suffix else path.name
    return path.with_name(f"{stem}.{stamp}.{ext}.bak")


def build_arg_parser(description: str) -> argparse.ArgumentParser:
    """Build the argument parser shared by both families-withdrawal tools."""
    parser = argparse.ArgumentParser(description=description)
    VerbosityConfiguration.set_arguments(parser)
    parser.add_argument(
        "-i", "--instance",
        type=str,
        default=None,
        help=(
            "Path to the GPF instance configuration file. "
            "When omitted, the instance is discovered via the DAE_DB_DIR "
            "environment variable, then by searching the current directory "
            "and its parents for a gpf_instance.yaml file."
        ),
    )
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
        "--no-backup",
        action="store_true",
        default=False,
        help=(
            "Do not create a backup of each modified file. By default a "
            "stamped <stem>.<stamp>.<ext>.bak sibling is written before any "
            "file is modified. Has no effect with --dry-run."
        ),
    )
    return parser
