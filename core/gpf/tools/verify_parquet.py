"""Tool to verify file-level structural integrity of parquet files."""
from __future__ import annotations

import argparse
import dataclasses
import datetime
import functools
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import pyarrow as pa
import pyarrow.parquet as pq
from gain.utils.verbosity_configuration import VerbosityConfiguration

EXIT_OK = 0
EXIT_FAILURES = 1
EXIT_USAGE = 2

PARQUET_SUFFIX = ".parquet"

DEFAULT_JOBS_CAP = 8

logger = logging.getLogger("verify_parquet")


@dataclass
class FileResult:
    """Outcome of verifying a single parquet file."""

    path: str
    ok: bool
    error_class: str | None = None
    message: str | None = None
    row_group: int | None = None


def verify_parquet_file(
    path: str, *, deep: bool = False,
) -> FileResult:
    """Verify file-level structural integrity of a single parquet file.

    Default check opens the file and parses footer + row-group metadata.
    ``deep=True`` additionally decodes every row group, catching data-page
    corruption that the metadata pass cannot see.
    """
    try:
        pf = pq.ParquetFile(path)
    except (OSError, pa.ArrowException) as err:
        return FileResult(
            path=path,
            ok=False,
            error_class=type(err).__name__,
            message=str(err),
        )

    if deep:
        for i in range(pf.num_row_groups):
            try:
                pf.read_row_group(i)
            except (OSError, pa.ArrowException) as err:
                return FileResult(
                    path=path,
                    ok=False,
                    error_class=type(err).__name__,
                    message=str(err),
                    row_group=i,
                )

    return FileResult(path=path, ok=True)


def _collect_parquet_files(path: str) -> list[str]:
    """Expand a single CLI path into a list of parquet files.

    Files are returned as-is. Directories are walked recursively for
    ``*.parquet`` (case-sensitive); dotfiles are skipped; symlinks are not
    followed.
    """
    if os.path.isfile(path):
        return [path]
    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.startswith("."):
                continue
            if name.endswith(PARQUET_SUFFIX):
                files.append(os.path.join(dirpath, name))
    return sorted(files)


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verify_parquet",
        description=(
            "Verify file-level structural integrity of parquet files. "
            "Walks directories recursively for *.parquet."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more parquet files or directories to verify.",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help=(
            "Force full row-group decode (catches data-page corruption). "
            "Slower but more thorough."
        ),
    )
    parser.add_argument(
        "-j", "--jobs",
        type=int,
        default=min((os.cpu_count() or 1), DEFAULT_JOBS_CAP),
        help=(
            "Number of worker threads. "
            f"Default min(cpu_count, {DEFAULT_JOBS_CAP})."
        ),
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        metavar="PATH",
        default=None,
        help="Write a structured JSON report to PATH in addition to logging.",
    )
    VerbosityConfiguration.set_arguments(parser)
    return parser


def _write_json_report(
    path: str, results: list[FileResult], *,
    deep: bool, started: str, finished: str,
) -> None:
    doc = {
        "tool": "verify_parquet",
        "deep": deep,
        "checked": len(results),
        "failures": sum(1 for r in results if not r.ok),
        "started": started,
        "finished": finished,
        "files": [
            {k: v for k, v in dataclasses.asdict(r).items() if v is not None}
            for r in results
        ],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit code."""
    parser = _build_argparser()
    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    for path in args.paths:
        if not os.path.exists(path):
            logger.error("path does not exist: %s", path)
            return EXIT_USAGE

    targets: list[str] = []
    for path in args.paths:
        targets.extend(_collect_parquet_files(path))

    if not targets:
        logger.error(
            "no parquet files found under: %s", ", ".join(args.paths),
        )
        return EXIT_USAGE

    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    check = functools.partial(verify_parquet_file, deep=args.deep)
    if args.jobs <= 1:
        results = [check(p) for p in targets]
    else:
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(check, targets))
    finished = datetime.datetime.now(datetime.timezone.utc).isoformat()
    failures = sum(1 for r in results if not r.ok)
    for r in results:
        if r.ok:
            logger.info("OK %s", r.path)
        else:
            attr = f" (row group {r.row_group})" if r.row_group is not None \
                else ""
            logger.error(
                "FAIL %s: %s: %s%s",
                r.path, r.error_class, r.message, attr,
            )
    logger.info("Checked %d files, %d failures", len(results), failures)

    if args.json_path is not None:
        _write_json_report(
            args.json_path, results,
            deep=args.deep, started=started, finished=finished,
        )

    return EXIT_OK if failures == 0 else EXIT_FAILURES


if __name__ == "__main__":
    raise SystemExit(main())
