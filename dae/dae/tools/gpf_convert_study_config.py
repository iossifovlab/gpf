#!/usr/bin/env python
import argparse
import logging

import yaml

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("gpf_convert_study_config")


def load_study_config(study_config_filename: str) -> dict:
    """Load study config."""
    config = GPFConfigParser.load_config_raw(
        study_config_filename,
    )

    return config


def main(
    gpf_instance: GPFInstance | None = None,
    argv: list[str] | None = None,
) -> None:
    """Convert GPF genotype data configuration to YAML."""
    description = "Tool to convert GPF genotype data configuration to YAML"
    parser = argparse.ArgumentParser(description=description)
    VerbosityConfiguration.set_arguments(parser)

    parser.add_argument(
        "--show-studies",
        help="This option will print available "
        "genotype data IDs",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--output", "-o",
        help="Specify output file name",
        default="study_config.yaml",
        action="store",
    )
    parser.add_argument(
        "study_config",
        help="Specify study config file to convert",
    )

    args = parser.parse_args(argv)

    VerbosityConfiguration.set(args)
    logging.getLogger("impala").setLevel(logging.WARNING)

    if gpf_instance is None:
        gpf_instance = GPFInstance.build()

    study_config_filename = args.study_config
    logger.info("converting genotype data: %s", study_config_filename)

    study_config = load_study_config(study_config_filename)

    with open(args.output, "wt") as out:
        out.write(yaml.dump(
            study_config,
            default_flow_style=False,
            sort_keys=False,
        ))
