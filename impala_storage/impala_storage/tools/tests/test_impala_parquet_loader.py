# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Callable

from dae.gpf_instance.gpf_instance import GPFInstance
from impala_storage.tools.impala_parquet_loader import main


def test_impala_parquet_loader_partitioned(
    fixture_dirname: Callable,
    gpf_instance_2013: GPFInstance,
) -> None:

    pedigree_path = fixture_dirname(
        "backends/test_partition2/pedigree/pedigree.parquet")
    variants_path = fixture_dirname(
        "backends/test_partition2/variants")

    argv = [
        "test_study_impala_01",
        pedigree_path,
        variants_path,
        "--gs",
        "genotype_impala",
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()

    genotype_data = gpf_instance_2013.get_genotype_data("test_study_impala_01")
    assert genotype_data is not None


def test_impala_parquet_loader_no_partition(
    fixture_dirname: Callable,
    gpf_instance_2013: GPFInstance,
) -> None:

    pedigree_path = fixture_dirname(
        "studies/quads_f1_impala/data/pedigree/"
        "quads_f1_impala_pedigree.parquet")
    variants_path = fixture_dirname(
        "studies/quads_f1_impala/data/variants")

    argv = [
        "test_study_impala_02",
        pedigree_path,
        variants_path,
        "--gs",
        "genotype_impala",
    ]

    main(argv, gpf_instance_2013)

    gpf_instance_2013.reload()

    genotype_data = gpf_instance_2013.get_genotype_data("test_study_impala_02")
    assert genotype_data is not None
