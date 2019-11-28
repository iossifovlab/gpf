import pytest
import numpy as np
from dae.backends.impala.parquet_io import ParquetPartitionDescription
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryAllele, SummaryVariant

summary_alleles_chr1 = [
    SummaryAllele('1', 11539, 'T', None, 0, 0),
    SummaryAllele('1', 11539, 'T', 'TA', 0, 1),
    SummaryAllele('1', 11539, 'T', 'TG', 0, 2),
]

summary_alleles_chr2 = [
    SummaryAllele('2', 11539, 'T', None, 0, 0),
    SummaryAllele('2', 11539, 'T', 'TA', 0, 1),
    SummaryAllele('2', 11539, 'T', 'TG', 0, 2),
]


@pytest.mark.parametrize(
    'chromosomes, region_length, summary_alleles, expected', [
        (['1', '2'], 1000, summary_alleles_chr1, '1_11'),
        (['1', '2'], 1000, summary_alleles_chr2, '2_11'),
        (['1'], 1000, summary_alleles_chr1, '1_11'),
        (['2'], 1000, summary_alleles_chr1, 'other_11')
    ])
def test_parquet_region_bin(fam1, gt, chromosomes,
                            region_length, summary_alleles, expected):
    sv = SummaryVariant(summary_alleles)
    fv = FamilyVariant.from_summary_variant(sv, fam1, gt)
    pd = ParquetPartitionDescription(
        chromosomes, region_length
    )
    region_bin = pd._evaluate_region_bin(fv)
    for fa in fv.alleles:
        assert region_bin == expected
        assert pd.evaluate_variant_filename(fa) == \
            f'region_bin={region_bin}/variants_region_bin_{region_bin}.parquet'


def test_parquet_family_bin(fam1, fam2, gt):
    sv = SummaryVariant(summary_alleles_chr1)
    fv1 = FamilyVariant.from_summary_variant(sv, fam1, gt)
    fv2 = FamilyVariant.from_summary_variant(sv, fam2, gt)
    family_bin_size = 10
    pd = ParquetPartitionDescription(
        ['1'], 1000, family_bin_size
    )
    for fa1, fa2 in zip(fv1.alleles, fv2.alleles):
        assert pd._evaluate_family_bin(fa1) == 9
        assert pd._evaluate_family_bin(fa2) == 6
        assert pd.evaluate_variant_filename(fa1) == \
            f'region_bin=1_11/family_bin=9/' + \
            f'variants_region_bin_1_11_family_bin_9.parquet'
        assert pd.evaluate_variant_filename(fa2) == \
            f'region_bin=1_11/family_bin=6/' + \
            f'variants_region_bin_1_11_family_bin_6.parquet'


@pytest.mark.parametrize('attributes, rare_boundary, expected', [
        ({'af_allele_count': 1}, 5, 1),
        ({'af_allele_count': 10, 'af_allele_freq': 2}, 5, 2),
        ({'af_allele_count': 10, 'af_allele_freq': 5}, 5, 3),
        ({'af_allele_count': 10, 'af_allele_freq': 6}, 5, 3),
        ({'af_allele_count': 10, 'af_allele_freq': 50}, 10, 3),
    ])
def test_parquet_frequency_bin(fam1, gt, attributes, rare_boundary, expected):
    summary_alleles = [
        SummaryAllele('1', 11539, 'T', None, 0, 0, attributes=attributes)
    ] * 3
    sv = SummaryVariant(summary_alleles)
    fv = FamilyVariant.from_summary_variant(sv, fam1, gt)
    pd = ParquetPartitionDescription(
        ['1'], 1000, rare_boundary=rare_boundary
    )

    for fa in fv.alleles:
        assert pd._evaluate_frequency_bin(fa) == expected
        assert pd.evaluate_variant_filename(fa) == \
            f'region_bin=1_11/frequency_bin={expected}/' + \
            f'variants_region_bin_1_11_frequency_bin_{expected}.parquet'


@pytest.mark.parametrize('eff1, eff2, eff3, coding_effect_types, expected', [
        (
            'synonymous!SAMD11:synonymous!NM_152486_1:40/68',
            'synonymous!SAMD11:synonymous!NM_152486_1:40/68',
            'synonymous!SAMD11:synonymous!NM_152486_1:40/68',
            ['synonymous'],
            [0, 1, 1, 1]
        ),
        (
            'synonymous!SAMD11:synonymous!NM_152486_1:40/68',
            'synonymous!SAMD11:synonymous!NM_152486_1:40/68',
            'synonymous!SAMD11:synonymous!NM_152486_1:40/68',
            ['missense'],
            [0, 0, 0, 0]
        ),
        (
            'synonymous!SAMD11:synonymous!NM_152486_1:40/68',
            'synonymous!SAMD11:synonymous!NM_152486_1:40/68',
            'synonymous!SAMD11:synonymous!NM_152486_1:40/68',
            ['missense', 'synonymous'],
            [0, 1, 1, 1]
        ),
        (
            'synonymous!SAMD11:synonymous!NM_152486_1:40/68',
            'missense!SAMD11:missense!NM_152486_1:54/681(Ser->Arg)',
            'intergenic!intergenic:intergenic!intergenic:intergenic',
            ['synonymous'],
            [0, 1, 0, 0]
        ),
        (
            'synonymous!SAMD11:synonymous!NM_152486_1:40/68',
            'missense!SAMD11:missense!NM_152486_1:54/681(Ser->Arg)',
            'missense!SAMD11:missense!NM_152486_1:54/681(Ser->Arg)',
            ['nonsense', 'intergenic'],
            [0, 0, 0, 0]
        ),
    ])
def test_parquet_coding_bin(fam1, gt, eff1, eff2, eff3,
                            coding_effect_types, expected):
    summary_alleles = [
            SummaryAllele('1', 11539, 'T', None, 0, 0),
            SummaryAllele('1', 11539, 'T', 'G', 0, 1,
                          attributes={'effects': eff1}),
            SummaryAllele('1', 11539, 'T', 'C', 0, 2,
                          attributes={'effects': eff2}),
            SummaryAllele('1', 11539, 'T', 'A', 0, 3,
                          attributes={'effects': eff3}),
    ]
    gt = np.array([[0, 1, 0], [2, 0, 3]], dtype='int8')
    sv = SummaryVariant(summary_alleles)
    fv = FamilyVariant.from_summary_variant(sv, fam1, gt)
    pd = ParquetPartitionDescription(
        ['1'], 1000, coding_effect_types=coding_effect_types
    )
    for fa, ex in zip(fv.alleles, expected):
        assert pd._evaluate_coding_bin(fa) == ex
        assert pd.evaluate_variant_filename(fa) == \
            f'region_bin=1_11/coding_bin={ex}/' + \
            f'variants_region_bin_1_11_coding_bin_{ex}.parquet'
