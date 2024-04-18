# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.variants.variant import (
    SummaryAllele,
    SummaryVariant,
    SummaryVariantFactory,
)


@pytest.mark.skip(reason="See comment in create_reference_allele")
@pytest.mark.parametrize("allele_counts, alternatives", [
    ([6, 2], [None, "G"]),
    ([6, 2, 2], [None, "G", "A"]),
    ([0, 2, 2], [None, "G", "A"]),
    ([1, 2, 3, 4, 0], [None, "G", "GG", "GGG", "AAA"]),
])
def test_allele_frequencies(allele_counts, alternatives):
    sum_allele_counts = sum(allele_counts)
    allele_freqs = [cnt / sum_allele_counts for cnt in allele_counts]
    alleles = []
    for i, (cnt, alternative) in enumerate(zip(allele_counts, alternatives)):
        alleles.append(SummaryAllele(
            "chr1", 11539, "T", alternative,
            end_position=0, summary_index=0, allele_index=i,
            attributes={
                "af_allele_count": cnt, "af_allele_freq": allele_freqs[i],
                "af_ref_allele_count": allele_counts[0],
                "af_ref_allele_freq": allele_freqs[0],
            },
        ))
    in_sv = SummaryVariant(alleles)
    for i, allele in enumerate(in_sv.alleles):
        assert allele.is_reference_allele == (i == 0)
        assert allele.frequency == allele_freqs[i]

    records = in_sv.to_record
    out_sv = SummaryVariantFactory.summary_variant_from_records(records)

    assert_summary_variants_equal(in_sv, out_sv)


@pytest.mark.skip(reason="See comment in create_reference_allele")
def test_multiple_to_records_iterations():
    in_sv = SummaryVariant([
        SummaryAllele(
            "chr1", 11539, "T", None,
            end_position=0, summary_index=0, allele_index=0,
            attributes={
                "af_allele_count": 2, "af_allele_freq": 25.0,
            },
        ),
        SummaryAllele(
            "chr1", 11539, "T", "G",
            end_position=0, summary_index=0, allele_index=1,
            attributes={
                "af_allele_count": 6, "af_allele_freq": 75.0,
                "af_ref_allele_count": 2, "af_ref_allele_freq": 25.0,
            },
        ),
    ])

    records = in_sv.to_record
    out_sv = SummaryVariantFactory.summary_variant_from_records(records)
    num_iterations = 2
    for _ in range(num_iterations):
        records = out_sv.to_record
        out_sv = SummaryVariantFactory.summary_variant_from_records(records)

    assert_summary_variants_equal(in_sv, out_sv)


def assert_summary_variants_equal(in_sv, out_sv):
    assert in_sv.allele_count == out_sv.allele_count
    assert in_sv.svuid == out_sv.svuid

    for in_allele, out_allele in zip(in_sv.alleles, out_sv.alleles):
        assert_alleles_equal(in_allele, out_allele)


def assert_alleles_equal(in_allele, out_allele):
    assert in_allele.summary_index == out_allele.summary_index
    assert in_allele.allele_index == out_allele.allele_index
    assert in_allele.variant_type == out_allele.variant_type
    assert in_allele.transmission_type == out_allele.transmission_type
    assert in_allele.effects == out_allele.effects
    assert in_allele.chromosome == out_allele.chromosome
    assert in_allele.frequency == out_allele.frequency
    assert str(in_allele) == str(out_allele)
