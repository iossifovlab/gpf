# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
import pytest

from dae.variants.core import Allele

from dae.variants.variant import SummaryVariantFactory


def relative_to_this_test_folder(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.fixture(scope="session")
def work_dir():
    return relative_to_this_test_folder("fixtures")


@pytest.fixture
def phastcons100way_variants_expected():
    variants_records = [
        [{"chrom": "1", "position": 10918}],
        [{"chrom": "1", "position": 10919}],
        [{"chrom": "1", "position": 10920}],
        [{"chrom": "1", "position": 10921}],
        [{"chrom": "1", "position": 10922}],
        [{"chrom": "1", "position": 10923}],
        [{"chrom": "2", "position": 20000}],
        [{"chrom": "2", "position": 20001}],
        [{"chrom": "2", "position": 20004}],
        [{"chrom": "2", "position": 20005}]
    ]
    variants = [
        SummaryVariantFactory.blank_summary_variant_from_records(rec)
        for rec in variants_records
    ]
    expected = [
        0.253,
        0.251,
        0.249,
        0.247,
        0.245,
        0.243,
        0.003,
        0.011,
        0.004,
        0.001
    ]

    return list(zip(variants, expected))


@pytest.fixture
def phastcons100way_indel_variants_expected():
    variants_records = [
        [{"chrom": "1", "position": 10919,
         "reference": "A", "alternative": "ATG"}],
        [{"chrom": "1", "position": 10920,
         "reference": "G", "alternative": "GAT"}],
        [{"chrom": "1", "position": 10930,
         "reference": "GATA", "alternative": "GAT"}],
        [{"chrom": "1", "position": 10930,
         "reference": "GATA", "alternative": "G"}],
        [{"chrom": "1", "position": 10933,
         "reference": "GATA", "alternative": "GTAA"}],
        [{"chrom": "1", "position": 10933,
         "reference": "GATA", "alternative": "GCC"}],
    ]
    variants = [
        SummaryVariantFactory.blank_summary_variant_from_records(rec)
        for rec in variants_records
    ]
    expected = [
        0.251, 0.249, 0.2145, 0.2145, 0.2011666666666667, 0.2011666666666667
    ]

    return list(zip(variants, expected))


@pytest.fixture
def position_agg_mean_variants_expected():
    variants_records = [
        [{"chrom": "1", "position": 11072,
         "reference": "GGGA", "alternative": "G"}],
    ]
    variants = [
        SummaryVariantFactory.blank_summary_variant_from_records(rec)
        for rec in variants_records
    ]
    expected = [0.003400000045076013]

    return list(zip(variants, expected))


@pytest.fixture
def cadd_variants_expected():
    variants_records = [
        [{
            "chrom": "1", "position": 10914,
            "reference": "C", "alternative": "A"
        }],
        [{
            "chrom": "1", "position": 10914,
            "reference": "C", "alternative": "G"
        }],
        [{
            "chrom": "1", "position": 10914,
            "reference": "C", "alternative": "T"
        }],
        [{
            "chrom": "1", "position": 10924,
            "reference": "C", "alternative": "A"
        }],
        [{
            "chrom": "1", "position": 10924,
            "reference": "C", "alternative": "G"
        }],
        [{
            "chrom": "1", "position": 10924,
            "reference": "C", "alternative": "T"
        }],
    ]
    variants = [
        SummaryVariantFactory.blank_summary_variant_from_records(rec)
        for rec in variants_records
    ]

    expected = [
        {
            "cadd_raw": 0.381392, "cadd_phred": 6.410
        },
        {
            "cadd_raw": 0.407661, "cadd_phred": 6.695
        },
        {
            "cadd_raw": 0.424578, "cadd_phred": 6.874
        },
        {
            "cadd_raw": 0.389901, "cadd_phred": 6.504
        },
        {
            "cadd_raw": 0.416170, "cadd_phred": 6.786
        },
        {
            "cadd_raw": 0.433087, "cadd_phred": 6.962
        },
    ]

    return list(zip(variants, expected))


@pytest.fixture
def cadd_indel_variants_expected():
    variants_records = [
        [{
            "chrom": "1", "position": 10915,
            "reference": "G", "alternative": "GTA"
        }],
        [{
            "chrom": "1", "position": 10920,
            "reference": "GAG", "alternative": "G"
        }],
        [{
            "chrom": "1", "position": 10920,
            "reference": "GAG", "alternative": "GTAG"
        }],
    ]
    variants = [
        SummaryVariantFactory.blank_summary_variant_from_records(rec)
        for rec in variants_records
    ]

    expected = [
        {
            "cadd_raw": 0.412572, "cadd_phred": 6.745333333333334
        },
        {
            "cadd_raw": 0.4407, "cadd_phred": 7.01775
        },
        {
            "cadd_raw": 0.4799115, "cadd_phred": 7.40450
        },
    ]

    return list(zip(variants, expected))


@pytest.fixture
def frequency_variants_expected():
    variants_records = [
        [{
            "chrom": "1", "position": 20000,
            "reference": "T", "alternative": "A",
            "variant_type": Allele.Type.substitution
        }],
        [{
            "chrom": "1", "position": 20000,
            "reference": "T", "alternative": "C",
            "variant_type": Allele.Type.substitution
        }],
        [{
            "chrom": "1", "position": 20000,
            "reference": "T", "alternative": "G",
            "variant_type": Allele.Type.substitution
        }],
        [{
            "chrom": "1", "position": 20001,
            "reference": "C", "alternative": "A",
            "variant_type": Allele.Type.substitution
        }],
        [{
            "chrom": "1", "position": 20001,
            "reference": "C", "alternative": "G",
            "variant_type": Allele.Type.substitution
        }],
        [{
            "chrom": "1", "position": 20001,
            "reference": "C", "alternative": "T",
            "variant_type": Allele.Type.substitution
        }],
    ]
    variants = [
        SummaryVariantFactory.blank_summary_variant_from_records(rec)
        for rec in variants_records
    ]

    expected = [
        {
            "alt_freq": 0.1, "alt_freq2": 0.8
        },
        {
            "alt_freq": 0.2, "alt_freq2": 0.9
        },
        {
            "alt_freq": 0.3, "alt_freq2": 1.0
        },
        {
            "alt_freq": 0.4, "alt_freq2": 1.1
        },
        {
            "alt_freq": 0.5, "alt_freq2": 1.2
        },
        {
            "alt_freq": 0.6, "alt_freq2": 1.3
        },
    ]

    return list(zip(variants, expected))


@pytest.fixture
def annotation_config(fixture_dirname):
    return fixture_dirname("annotation.yaml")
