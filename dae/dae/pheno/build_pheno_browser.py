import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from box import Box

from dae.pheno.pheno_data import PhenotypeData
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

    TaskGraphCli.add_arguments(parser, use_commands=False)

    return parser


def build_pheno_browser(
    pheno_data: PhenotypeData,
    pheno_regressions: Box | None = None,
    **kwargs: dict[str, Any],
) -> None:
    """Calculate and save pheno browser values to db."""

    pheno_data_dir = Path(pheno_data.config["conf_dir"])
    images_dir = pheno_data_dir / "images"
    images_dir.mkdir(exist_ok=True)

    prep = PreparePhenoBrowserBase(
        pheno_data, pheno_data_dir, pheno_regressions, images_dir)
    prep.run(**kwargs)


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
