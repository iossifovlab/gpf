import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from box import Box

from dae.pheno.browser import PhenoBrowser
from dae.pheno.pheno_data import PhenotypeData
from dae.pheno.pheno_import import IMPORT_METADATA_TABLE, ImportManifest
from dae.pheno.prepare_data import PreparePhenoBrowserBase
from dae.pheno.registry import PhenoRegistry
from dae.task_graph.cli_tools import TaskGraphCli

logger = logging.getLogger(__name__)


def pheno_cli_parser() -> argparse.ArgumentParser:
    """Construct argument parser for phenotype import tool."""
    parser = argparse.ArgumentParser(
        description="phenotype browser generation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "pheno_dir", help="Path to pheno directory.",
    )
    parser.add_argument("--phenotype-data-id", help="Phenotype data ID")

    parser.add_argument("-n", "--dry-run", action="store_true")

    TaskGraphCli.add_arguments(parser, use_commands=False)

    return parser


def must_rebuild(pheno_data: PhenotypeData, browser: PhenoBrowser) -> bool:
    """Check if a rebuild is required according to manifests."""
    manifests = {
        manifest.import_config.id: manifest
        for manifest in
        ImportManifest.from_table(browser.connection, IMPORT_METADATA_TABLE)
    }

    if len(manifests) == 0:
        logger.warning("No manifests found in browser; either fresh or legacy")
        return True

    pheno_data_manifests = {
        manifest.import_config.id: manifest
        for manifest in
        ImportManifest.from_phenotype_data(pheno_data)
    }
    if len(set(manifests).symmetric_difference(pheno_data_manifests)) > 0:
        logger.warning("Manifest count mismatch between input and browser")
        return True

    is_outdated = False
    for pheno_id, pheno_manifest in pheno_data_manifests.items():
        browser_manifest = manifests[pheno_id]
        if browser_manifest.is_older_than(pheno_manifest):
            logger.warning("Browser manifest outdated for %s", pheno_id)
            is_outdated = True
    return is_outdated


def build_pheno_browser(
    pheno_data: PhenotypeData,
    pheno_regressions: Box | None = None,
    **kwargs: dict[str, Any],
) -> None:
    """Calculate and save pheno browser values to db."""

    pheno_data_dir = Path(pheno_data.config["conf_dir"])
    images_dir = pheno_data_dir / "images"
    images_dir.mkdir(exist_ok=True)
    browser = PhenotypeData.create_browser(
        pheno_data, read_only=False,
    )
    rebuild = must_rebuild(pheno_data, browser)
    if (rebuild or kwargs["force"]) and not kwargs["dry_run"]:
        prep = PreparePhenoBrowserBase(
            pheno_data, browser, pheno_data_dir, pheno_regressions, images_dir)
        prep.run(**kwargs)
    else:
        if not rebuild:
            print("No need to rebuild")
        sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv[1:]

        # Setup argument parser

    parser = pheno_cli_parser()
    args = parser.parse_args(argv)
    if args.pheno_dir is None:
        raise ValueError("Missing phenotype directory argument.")

    if args.phenotype_data_id is None:
        raise ValueError("Missing phenotype data ID argument.")

    registry = PhenoRegistry.from_directory(Path(args.pheno_dir))
    pheno_data = registry.get_phenotype_data(args.phenotype_data_id)
    kwargs = vars(args)

    regressions = pheno_data.config.regression

    build_pheno_browser(pheno_data, regressions, **kwargs)

    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
