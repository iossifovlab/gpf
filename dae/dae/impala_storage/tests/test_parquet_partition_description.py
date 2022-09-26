# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
import numpy as np

from dae.impala_storage.parquet_io import ParquetPartitionDescriptor, \
    NoPartitionDescriptor
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryAllele, SummaryVariant

summary_alleles_chr1 = [
    SummaryAllele("1", 11539, "T", None, 0, 0),
    SummaryAllele("1", 11539, "T", "TA", 0, 1),
    SummaryAllele("1", 11539, "T", "TG", 0, 2),
]

summary_alleles_chr2 = [
    SummaryAllele("2", 11539, "T", None, 0, 0),
    SummaryAllele("2", 11539, "T", "TA", 0, 1),
    SummaryAllele("2", 11539, "T", "TG", 0, 2),
]


@pytest.mark.parametrize(
    "chromosomes, region_length, summary_alleles, expected",
    [
        (["1", "2"], 1000, summary_alleles_chr1, "1_11"),
        (["1", "2"], 1000, summary_alleles_chr2, "2_11"),
        (["1"], 1000, summary_alleles_chr1, "1_11"),
        (["2"], 1000, summary_alleles_chr1, "other_11"),
    ],
)
def test_parquet_region_bin(
    fam1, genotype, chromosomes, region_length, summary_alleles, expected
):
    sv = SummaryVariant(summary_alleles)
    fv = FamilyVariant(sv, fam1, genotype, None)
    part_desc = ParquetPartitionDescriptor(chromosomes, region_length)
    region_bin = part_desc._evaluate_region_bin(fv)
    for fa in fv.alleles:
        assert region_bin == expected
        assert (
            part_desc.variant_filename(fa)
            == f"region_bin={region_bin}/variants_region_bin_{region_bin}"
            f".parquet"
        )


def test_parquet_family_bin(fam1, fam2, genotype):
    sv = SummaryVariant(summary_alleles_chr1)
    fv1 = FamilyVariant(sv, fam1, genotype, None)
    fv2 = FamilyVariant(sv, fam2, genotype, None)

    family_bin_size = 10
    part_desc = ParquetPartitionDescriptor(["1"], 1000, family_bin_size)
    for fa1, fa2 in zip(fv1.alleles, fv2.alleles):
        assert part_desc._evaluate_family_bin(fa1) == 9
        assert part_desc._evaluate_family_bin(fa2) == 6
        assert (
            part_desc.variant_filename(fa1)
            == "region_bin=1_11/family_bin=9/"
            "variants_region_bin_1_11_family_bin_9.parquet"
        )
        assert (
            part_desc.variant_filename(fa2)
            == "region_bin=1_11/family_bin=6/"
            "variants_region_bin_1_11_family_bin_6.parquet"
        )


@pytest.mark.parametrize(
    "attributes, rare_boundary, expected",
    [
        ({"af_allele_count": 1}, 5, 1),
        ({"af_allele_count": 10, "af_allele_freq": 2}, 5, 2),
        ({"af_allele_count": 10, "af_allele_freq": 5}, 5, 3),
        ({"af_allele_count": 10, "af_allele_freq": 6}, 5, 3),
        ({"af_allele_count": 10, "af_allele_freq": 50}, 10, 3),
    ],
)
def test_parquet_frequency_bin(fam1, genotype, attributes, rare_boundary,
                               expected):
    summary_alleles = [
        SummaryAllele("1", 11539, "T", None, 0, 0, attributes=attributes)
    ] * 3
    sv = SummaryVariant(summary_alleles)
    fv = FamilyVariant(sv, fam1, genotype, None)
    part_desc = ParquetPartitionDescriptor(["1"], 1000,
                                           rare_boundary=rare_boundary)

    for fa in fv.alleles:
        assert part_desc._evaluate_frequency_bin(fa) == expected
        assert (
            part_desc.variant_filename(fa)
            == f"region_bin=1_11/frequency_bin={expected}/"
            + f"variants_region_bin_1_11_frequency_bin_{expected}.parquet"
        )


@pytest.mark.parametrize(
    "eff1, eff2, eff3, coding_effect_types, expected",
    [
        (
            "synonymous!SAMD11:synonymous!NM_152486_1:SAMD11:synonymous:40/68",
            "synonymous!SAMD11:synonymous!NM_152486_1:SAMD11:synonymous:40/68",
            "synonymous!SAMD11:synonymous!NM_152486_1:SAMD11:synonymous:40/68",
            ["synonymous"],
            [0, 1, 1, 1],
        ),
        (
            "synonymous!SAMD11:synonymous!NM_152486_1:SAMD11:synonymous:40/68",
            "synonymous!SAMD11:synonymous!NM_152486_1:SAMD11:synonymous:40/68",
            "synonymous!SAMD11:synonymous!NM_152486_1:SAMD11:synonymous:40/68",
            ["missense"],
            [0, 0, 0, 0],
        ),
        (
            "synonymous!SAMD11:synonymous!NM_152486_1:SAMD11:synonymous:40/68",
            "synonymous!SAMD11:synonymous!NM_152486_1:SAMD11:synonymous:40/68",
            "synonymous!SAMD11:synonymous!NM_152486_1:SAMD11:synonymous:40/68",
            ["missense", "synonymous"],
            [0, 1, 1, 1],
        ),
        (
            "synonymous!SAMD11:synonymous!"
            "NM_152486_1:SAMD11:synonymous:40/68",
            "missense!SAMD11:missense!"
            "NM_152486_1:SAMD11:missense:54/681(Ser->Arg)",
            "intergenic!intergenic:intergenic!"
            "intergenic:intergenic:intergenic:intergenic",
            ["synonymous"],
            [0, 1, 0, 0],
        ),
        (
            "synonymous!SAMD11:synonymous!"
            "NM_152486_1:SAMD11:synonymous:40/68",
            "missense!SAMD11:missense!"
            "NM_152486_1:SAMD11:missense:54/681(Ser->Arg)",
            "missense!SAMD11:missense!"
            "NM_152486_1:SAMD11:missense:54/681(Ser->Arg)",
            ["nonsense", "intergenic"],
            [0, 0, 0, 0],
        ),
    ],
)
def test_parquet_coding_bin(
    fam1, eff1, eff2, eff3, coding_effect_types, expected
):
    summary_alleles = [
        SummaryAllele("1", 11539, "T", None, 0, 0),
        SummaryAllele(
            "1", 11539, "T", "G", 0, 1, attributes={"effects": eff1}
        ),
        SummaryAllele(
            "1", 11539, "T", "C", 0, 2, attributes={"effects": eff2}
        ),
        SummaryAllele(
            "1", 11539, "T", "A", 0, 3, attributes={"effects": eff3}
        ),
    ]
    genotype = np.array([[0, 1, 0], [2, 0, 3]], dtype="int8")
    sv = SummaryVariant(summary_alleles)
    fv = FamilyVariant(sv, fam1, genotype, None)
    part_desc = ParquetPartitionDescriptor(
        ["1"], 1000, coding_effect_types=coding_effect_types
    )
    for fa, ex in zip(fv.alleles, expected):
        assert part_desc._evaluate_coding_bin(fa) == ex
        assert (
            part_desc.variant_filename(fa)
            == f"region_bin=1_11/coding_bin={ex}/"
            + f"variants_region_bin_1_11_coding_bin_{ex}.parquet"
        )


@pytest.mark.parametrize("filename", [
    "region_bin=1_0/frequency_bin=1/coding_bin=1/family_bin=0/"
    "variants_region_bin_1_0_frequency_bin_1_coding_bin_1_family_bin_0"
    ".parquet",

    "region_bin=1_0/frequency_bin=1/coding_bin=1/family_bin=0/"
    "variants_region_bin_1_0_frequency_bin_1_coding_bin_1_family_bin_0"
    "_bucket_index_0.parquet",
])
def test_variant_filename_basedir(filename):
    part_desc = ParquetPartitionDescriptor(
        ["1"], 30_000_000,
        family_bin_size=10,
        coding_effect_types=["missense", "synonymous"],
        rare_boundary=5
    )

    res = part_desc.variants_filename_basedir(
        f"AGRE_WG_859_variants.parquet/{filename}")
    assert res == "AGRE_WG_859_variants.parquet/"

    res = part_desc.variants_filename_basedir(f"ala/bala/nica/{filename}")
    assert res == "ala/bala/nica/"

    bad_res = part_desc.variants_filename_basedir(
        f"ala/bala/nica/{filename}_tata")
    assert bad_res is None

    bad_res = part_desc.variants_filename_basedir(filename)
    assert bad_res is None

    res = part_desc.variants_filename_basedir(
        f"hdfs://localhost:8020/ala/bala/nica/{filename}")
    assert res == "hdfs://localhost:8020/ala/bala/nica/"


def test_no_partition_variant_filename_basedir():
    filename = "gosho_variants.parquet"

    part_desc = NoPartitionDescriptor()

    res = part_desc.variants_filename_basedir(
        f"AGRE_WG_859_variants.parquet/{filename}")
    assert res == "AGRE_WG_859_variants.parquet/"

    res = part_desc.variants_filename_basedir(f"ala/bala/nica/{filename}")
    assert res == "ala/bala/nica/"

    bad_res = part_desc.variants_filename_basedir(
        f"ala/bala/nica/{filename}_tata")
    assert bad_res is None

    bad_res = part_desc.variants_filename_basedir(filename)
    assert bad_res is None

    res = part_desc.variants_filename_basedir(
        f"hdfs://localhost:8020/ala/bala/nica/{filename}")
    assert res == "hdfs://localhost:8020/ala/bala/nica/"
