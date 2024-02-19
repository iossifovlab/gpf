# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Callable

from dae.utils.regions import Region
from dae.parquet.partition_descriptor import PartitionDescriptor
from impala2_storage.schema2.impala_variants import ImpalaVariants


def test_import_and_query(testing_study_backend: ImpalaVariants) -> None:
    family_variants = list(testing_study_backend.query_variants())
    summary_variants = list(testing_study_backend.query_summary_variants())

    # assert the number of summary and family allelies is as expected
    assert len(family_variants) == 5
    assert len(summary_variants) == 5
    # 5 reference and 10 alternative alleles
    assert sum(len(sv.alleles) for sv in summary_variants) == 15


def test_import_denovo_with_custome_range(
    import_test_study: Callable, tmpdir: pathlib.Path
) -> None:
    study_id = "testStudy"
    partition_description = PartitionDescriptor()
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


def test_query_variants_with_gene_symbols(
    testing_study_backend: ImpalaVariants
) -> None:
    effect_types = [
        "frame-shift", "nonsense", "splice-site", "no-frame-shift-newStop",
        "nonsense", "frame-shift", "splice-site", "no-frame-shift-newStop",
        "missense", "no-frame-shift", "noStart", "noEnd", "synonymous",
        "CNV+", "CNV-", "CDS"
    ]
    inheritance = [
        "not possible_denovo and not possible_omission",
        "any(denovo,omission,mendelian,missing)"
    ]

    summary_variants = list(testing_study_backend.query_summary_variants(
        genes=["SAMD11"],
        effect_types=effect_types,
        inheritance=inheritance,
    ))
    assert len(summary_variants) == 2

    family_variants = list(testing_study_backend.query_variants(
        genes=["SAMD11"],
        effect_types=effect_types,
        inheritance=inheritance,
    ))
    assert len(family_variants) == 2
