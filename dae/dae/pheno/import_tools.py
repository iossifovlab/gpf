import argparse
import os
import pathlib
import sys

import yaml
from pydantic import BaseModel

from dae.pheno.common import InferenceConfig
from dae.pheno.pheno_import import import_pheno_data
from dae.task_graph.cli_tools import TaskGraphCli


class _DataDictionary(BaseModel):
    file: str
    instrument_files: list[str]

    # {Instrument -> {Measure -> Description}}
    dictionary: dict[str, dict[str, str]]


class RegressionMeasure(BaseModel):
    instrument_name: str
    measure_name: str
    jitter: float
    display_name: str


class PhenoImportConfig(BaseModel):
    """Pheno import config."""
    id: str
    input_dir: str
    output_dir: str
    pedigree: str
    skip_pedigree_measures: bool
    # instrument_files: list[FilePath | DirectoryPath]
    instruments: str
    person_column: str
    inference_config: str | dict[str, InferenceConfig] | None = None
    data_dictionary: _DataDictionary | None = None
    regression_config: str | dict[str, RegressionMeasure] | None = None


def pheno_cli_parser() -> argparse.ArgumentParser:
    """Construct argument parser for phenotype import tool."""
    parser = argparse.ArgumentParser(
        description="phenotype database import tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project",
        help="Configuration for the phenotype import",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="count",
        help="Set the verbosity level. [default: %(default)s]",
    )
    TaskGraphCli.add_arguments(parser, use_commands=False)
    return parser


def map_config_to_args(
    args: argparse.Namespace,
    import_config: PhenoImportConfig,
) -> None:
    """Map config values to argparse arguments."""
    args.output = import_config.output_dir
    args.pheno_name = import_config.id
    if not os.path.isabs(import_config.instruments):
        args.instruments = os.path.join(
            import_config.input_dir, import_config.instruments,
        )
    if not os.path.isabs(import_config.pedigree):
        args.pedigree = os.path.join(
            import_config.input_dir, import_config.pedigree,
        )
    args.tab_separated = False
    args.person_column = import_config.person_column
    args.inference_config = import_config.inference_config
    args.skip_pheno_common = import_config.skip_pedigree_measures
    args.data_dictionary = import_config.data_dictionary
    if isinstance(import_config.regression_config, str) and \
       not os.path.isabs(import_config.regression_config):
        args.regression = os.path.join(
            import_config.input_dir, import_config.regression_config,
        )


def main(argv: list[str] | None = None) -> int:
    """Run phenotype import tool."""
    if argv is None:
        argv = sys.argv[1:]
    parser = pheno_cli_parser()
    args = parser.parse_args(argv)

    import_config = PhenoImportConfig.model_validate(
        yaml.safe_load(pathlib.Path(args.project).read_text()))
    map_config_to_args(args, import_config)
    import_pheno_data(args)

    return 0
