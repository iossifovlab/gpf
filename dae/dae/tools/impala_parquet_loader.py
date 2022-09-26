#!/usr/bin/env python
import os
import sys
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.impala_storage.import_commons import save_study_config
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.utils.dict_utils import recursive_dict_update


def parse_cli_arguments(argv, gpf_instance):
    parser = argparse.ArgumentParser(
        description="loading study parquet files in impala db",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "study_id",
        type=str,
        metavar="<study ID>",
        help="study ID to be loaded",
    )

    parser.add_argument(
        "pedigree",
        type=str,
        metavar="<Pedigree Filepath>",
        help="path to the pedigree file",
    )

    parser.add_argument(
        "variants",
        type=str,
        metavar="<Variants Parquet Directory>",
        help="path to directory which contains variants parquet data files",
    )

    default_genotype_storage_id = (
        gpf_instance.dae_config.genotype_storage.default
    )

    parser.add_argument(
        "--genotype-storage",
        "--gs",
        type=str,
        metavar="<Genotype Storage>",
        dest="genotype_storage",
        help="Genotype Storage which will be used for import "
        "[default: %(default)s]",
        default=default_genotype_storage_id,
    )

    parser.add_argument(
        "--study-config",
        type=str,
        metavar="<study config>",
        dest="study_config",
        help="Optional study configuration to use instead of default"
    )

    parser.add_argument(
        "--force", "-F",
        dest="force",
        action="store_true",
        help="allows overwriting configuration file in case "
        "target directory already contains such file",
        default=False
    )

    argv = parser.parse_args(argv)
    return argv


def main(argv=sys.argv[1:], gpf_instance=None):
    if gpf_instance is None:
        gpf_instance = GPFInstance()

    argv = parse_cli_arguments(argv, gpf_instance)

    genotype_storage_db = gpf_instance.genotype_storage_db
    genotype_storage = genotype_storage_db.get_genotype_storage(
        argv.genotype_storage
    )
    if not genotype_storage or (
            genotype_storage and not genotype_storage.is_impala()):
        print("missing or non-impala genotype storage")
        return

    assert os.path.exists(argv.variants)

    study_config = genotype_storage.impala_load_dataset(
        argv.study_id, argv.variants, argv.pedigree)

    if argv.study_config:
        input_config = GPFConfigParser.load_config_raw(argv.study_config)
        study_config = recursive_dict_update(study_config, input_config)

    study_config = StudyConfigBuilder(study_config).build_config()
    assert study_config is not None
    save_study_config(
        gpf_instance.dae_config, argv.study_id, study_config,
        force=argv.force)


if __name__ == "__main__":
    main(sys.argv[1:])
