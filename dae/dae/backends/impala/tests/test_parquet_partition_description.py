import pytest
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
    assert region_bin == expected
    assert pd.evaluate_variant_filename(fv) == \
        f'{region_bin}/variants_region_bin_{region_bin}.parquet'


def test_parquet_family_bin(fam1, fam2, gt):
    sv = SummaryVariant(summary_alleles_chr1)
    fv1 = FamilyVariant.from_summary_variant(sv, fam1, gt)
    fv2 = FamilyVariant.from_summary_variant(sv, fam2, gt)
    family_bin_size = 10
    pd = ParquetPartitionDescription(
        ['1'], 1000, family_bin_size
    )
    expected_fam_1 = hash(fv1.family_id) % family_bin_size
    expected_fam_2 = hash(fv2.family_id) % family_bin_size
    assert pd._evaluate_family_bin(fv1) == expected_fam_1
    assert pd._evaluate_family_bin(fv2) == expected_fam_2
    assert pd.evaluate_variant_filename(fv1) == \
        f'1_11/{expected_fam_1}/' + \
        f'variants_region_bin_1_11_family_bin_{expected_fam_1}.parquet'
    assert pd.evaluate_variant_filename(fv2) == \
        f'1_11/{expected_fam_2}/' + \
        f'variants_region_bin_1_11_family_bin_{expected_fam_2}.parquet'


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

    assert pd._evaluate_frequency_bin(fv) == expected
    assert pd.evaluate_variant_filename(fv) == \
        f'1_11/{expected}/' + \
        f'variants_region_bin_1_11_frequency_bin_{expected}.parquet'
