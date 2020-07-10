#!/usr/bin/env python
import os
import sys
import argparse

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.backends.impala.import_commons import save_study_config
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.backends.impala.parquet_io import ParquetPartitionDescriptor
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
        help="HDFS path to the pedigree file",
    )

    parser.add_argument(
        "variants",
        type=str,
        metavar="<Variants Parquet Directory>",
        help="HDFS path to directory which contains variants parquet files",
    )

    default_genotype_storage_id = (
        gpf_instance.dae_config.genotype_storage.default)

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
        "--partition-description",
        "--pd",
        type=str,
        metavar="<Partition Description>",
        dest="partition_description",
        help="Partition description file name",
        default=None,
    )

    parser.add_argument(
        "--variants-sample",
        "--vs",
        type=str,
        metavar="<variants sample file>",
        dest="variants_sample",
        help="Variants HDFS parquet sample file",
        default=None,
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
        genotype_storage and not genotype_storage.is_impala()
    ):
        print("missing or non-impala genotype storage")
        return

    hdfs_variants_dir = argv.variants
    hdfs_pedigree_file = argv.pedigree

    print("HDFS variants directory:", hdfs_variants_dir)
    print("HDFS pedigree file:", hdfs_pedigree_file)

    if argv.partition_description is not None:
        partition_config_file = argv.partition_description
        assert os.path.isfile(partition_config_file), partition_config_file
    else:
        root, _ = os.path.splitext(hdfs_variants_dir)
        partition_config_file = f"{root}.partition_description"
    print("partition_config_file:", partition_config_file)

    partition_description = None
    if os.path.isfile(partition_config_file):
        partition_description = ParquetPartitionDescriptor.from_config(
            partition_config_file, root_dirname=argv.variants)

    if partition_description is not None:
        variants_hdfs_sample_file = None
        if argv.variants_sample is not None:
            variants_hdfs_sample_file = argv.variants_sample

        study_config = genotype_storage.impala_import_dataset(
            argv.study_id,
            hdfs_pedigree_file,
            hdfs_variants_dir,
            variants_hdfs_sample_file=variants_hdfs_sample_file,
            partition_description=partition_description)
    else:
        has_variants = argv.variants is not None
        study_config = genotype_storage.impala_import_study(
            argv.study_id, hdfs_variants_dir,
            hdfs_pedigree_file, has_variants)

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
