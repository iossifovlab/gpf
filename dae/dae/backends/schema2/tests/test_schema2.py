# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.utils.regions import Region
from dae.backends.schema2.parquet_io import NoPartitionDescriptor


def test_import_and_query(testing_study_backend):
    family_variants = list(testing_study_backend.query_variants())
    summary_variants = list(testing_study_backend.query_summary_variants())

    # assert the number of summary and family allelies is as expected
    assert len(family_variants) == 5
    assert len(summary_variants) == 10
    # 10 reference and 18 alternative alleles
    assert sum(len(sv.alleles) for sv in summary_variants) == 28


def test_import_denovo_with_custome_range(
    import_test_study, partition_description, tmpdir
):
    study_id = "testStudy"
    partition_description = NoPartitionDescriptor()
    backend = import_test_study(
        study_id, str(tmpdir), partition_description, ["denovo_variants.txt"],
        loader_args={
            "regions": [Region("2", 30, 100)]
        }
    )

    family_variants = list(backend.query_variants())
    summary_variants = list(backend.query_summary_variants())

    assert len(family_variants) == 3
    assert len(summary_variants) == 3
    # 2 alleles per summary variant
    assert sum(len(sv.alleles) for sv in summary_variants) == 6
