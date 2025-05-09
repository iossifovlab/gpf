import argparse
import logging
import sys
from pathlib import Path

import yaml

from dae.pheno.browser import PhenoBrowser
from dae.pheno.common import PhenoImportConfig
from dae.pheno.db import PhenoDb
from dae.pheno.pheno_import import (
    load_instrument_descriptions,
    load_measure_descriptions,
)
from dae.task_graph.cli_tools import TaskGraphCli
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger(__name__)


def pheno_cli_parser() -> argparse.ArgumentParser:
    """Construct argument parser for phenotype import tool."""
    parser = argparse.ArgumentParser(
        description="phenotype browser generation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    VerbosityConfiguration.set_arguments(parser)
    parser.add_argument(
        "pheno_import_project",
        nargs="?",
        type=str,
        default=None,
        help="Path to pheno_import_project file.",
    )
    parser.add_argument(
        "--pheno-db-dir",
        help="Path to pheno DB dir to use.",
    )

    TaskGraphCli.add_arguments(parser, use_commands=False)
    return parser


def save_descriptions(
    instrument_descriptions: dict[str, str],
    measure_descriptions: dict[str, str],
    pheno_db: PhenoDb,
    pheno_browser_db: PhenoBrowser,
) -> None:
    """Save new descriptions to pheno db and pheno browser db."""
    pheno_db.save_instrument_descriptions(instrument_descriptions)
    pheno_browser_db.save_instrument_descriptions(instrument_descriptions)
    pheno_db.save_measure_descriptions(measure_descriptions)
    pheno_browser_db.save_measure_descriptions(measure_descriptions)


def main(argv: list[str] | None = None) -> int:
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv[1:]

    parser = pheno_cli_parser()
    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    assert args.pheno_db_dir is not None

    raw_config = yaml.safe_load(
        Path(args.pheno_import_project).absolute().read_text(),
    )

    project_path = Path(args.pheno_import_project).absolute()

    input_dir = Path(raw_config.get("input_dir", ""))
    if not input_dir.is_absolute():
        raw_config["input_dir"] = str(project_path.parent / input_dir)

    if raw_config.get("work_dir") is None:
        raw_config["work_dir"] = str(project_path.parent / raw_config["id"])

    import_config = PhenoImportConfig.model_validate(raw_config)

    measure_descriptions = load_measure_descriptions(
        import_config.input_dir,
        import_config.data_dictionary,
    )

    instrument_descriptions = load_instrument_descriptions(
        import_config.input_dir,
        import_config.instrument_dictionary,
    )

    db_folder = args.pheno_db_dir + "/pheno/" + import_config.id + "/"
    pheno_db = PhenoDb(
        db_folder + import_config.id + ".db", read_only=False)
    pheno_browser_db = PhenoBrowser(
        db_folder + import_config.id + "_browser.db", read_only=False)

    save_descriptions(
        instrument_descriptions,
        measure_descriptions,
        pheno_db,
        pheno_browser_db,
    )

    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
