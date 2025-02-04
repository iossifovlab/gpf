import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from box import Box

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pheno.browser import PhenoBrowser
from dae.pheno.pheno_data import (
    PhenotypeData,
    get_pheno_browser_images_dir,
    get_pheno_db_dir,
)
from dae.pheno.pheno_import import IMPORT_METADATA_TABLE, ImportManifest
from dae.pheno.prepare_data import PreparePhenoBrowserBase
from dae.pheno.registry import PhenoRegistry
from dae.pheno.storage import PhenotypeStorage, PhenotypeStorageRegistry
from dae.task_graph.cli_tools import TaskGraphCli

logger = logging.getLogger(__name__)


def pheno_cli_parser() -> argparse.ArgumentParser:
    """Construct argument parser for phenotype import tool."""
    parser = argparse.ArgumentParser(
        description="phenotype browser generation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "phenotype_data_id",
        help="ID of the phenotype data to build a browser database for.",
    )
    parser.add_argument(
        "--gpf-instance",
        help=("Path to GPF instance configuration to use for cache and images."),
    )
    parser.add_argument(
        "--pheno-db-dir",
        help=("Path to pheno DB dir to use."),
    )
    parser.add_argument(
        "--storage-dir",
        help=("Path to phenotype storage to use."),
    )
    parser.add_argument(
        "--cache-dir",
        help=("Path to output generated cache DB."),
    )
    parser.add_argument(
        "--images-dir",
        help=("Path to output images."),
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Do not write any output to the filesystem.",
    )

    TaskGraphCli.add_arguments(parser, use_commands=False)
    return parser


def must_rebuild(pheno_data: PhenotypeData, browser: PhenoBrowser) -> bool:
    """Check if a rebuild is required according to manifests."""
    manifests = {
        manifest.import_config.id: manifest
        for manifest in ImportManifest.from_table(
            browser.connection, IMPORT_METADATA_TABLE
        )
    }

    if len(manifests) == 0:
        logger.warning("No manifests found in browser; either fresh or legacy")
        return True

    pheno_data_manifests = {
        manifest.import_config.id: manifest
        for manifest in ImportManifest.from_phenotype_data(pheno_data)
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
    pheno_db_dir: Path,
    storage_registry: PhenotypeStorageRegistry,
    pheno_data: PhenotypeData,
    cache_dir: Path,
    images_dir: Path,
    pheno_regressions: Box | None = None,
    **kwargs: dict[str, Any],
) -> None:
    """Calculate and save pheno browser values to db."""

    browser = PhenotypeData.create_browser(
        pheno_data,
        read_only=False,
    )
    rebuild = must_rebuild(pheno_data, browser)
    if (rebuild or kwargs["force"]) and not kwargs["dry_run"]:
        prep = PreparePhenoBrowserBase(
            pheno_db_dir,
            storage_registry,
            pheno_data,
            browser,
            cache_dir,
            images_dir,
            pheno_regressions=pheno_regressions,
        )
        prep.run(**kwargs)
    else:
        if not rebuild:
            print("No need to rebuild")
        sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv[1:]

    parser = pheno_cli_parser()
    args = parser.parse_args(argv)
    if args.phenotype_data_id is None:
        raise ValueError("Missing phenotype data ID argument.")

    kwargs = vars(args)

    if args.pheno_db_dir is not None:
        pheno_db_dir = Path(args.pheno_db_dir)
        storage_registry = PhenotypeStorageRegistry()
        storage_config = {"id": "default_storage"}
        if args.storage_dir is not None:
            storage_config["base_dir"] = args.storage_dir
        else:
            storage_config["base_dir"] = str(pheno_db_dir)

        default_storage = PhenotypeStorage.from_config(storage_config)
        storage_registry.register_default_storage(default_storage)
        if args.cache_dir is not None:
            cache_dir = Path(args.cache_dir)
        else:
            cache_dir = pheno_db_dir

        if args.images_dir is not None:
            images_dir = Path(args.images_dir)
        else:
            images_dir = pheno_db_dir / "images"

        registry = PhenoRegistry(
            storage_registry,
            configurations=PhenoRegistry.load_configurations(
                str(pheno_db_dir),
            ),
        )
        pheno_data = registry.get_phenotype_data(args.phenotype_data_id)
    else:
        gpfi = GPFInstance.build(args.gpf_instance)

        pheno_data = gpfi.get_phenotype_data(args.phenotype_data_id)
        pheno_db_dir = Path(get_pheno_db_dir(gpfi.dae_config))
        storage_registry = gpfi.phenotype_storages
        cache_dir = gpfi.get_pheno_cache_path()
        images_dir = get_pheno_browser_images_dir(gpfi.dae_config)

    regressions = pheno_data.config.get("regression")
    del kwargs["pheno_db_dir"]
    del kwargs["cache_dir"]
    del kwargs["images_dir"]

    build_pheno_browser(
        pheno_db_dir,
        storage_registry,
        pheno_data,
        cache_dir,
        images_dir,
        pheno_regressions=regressions,
        **kwargs,
    )

    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
