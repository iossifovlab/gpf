# pylint: disable=W0621,C0114,C0116,W0212,W0613


def assert_summary_variants_equal(in_sv, out_sv):
    assert in_sv.allele_count == out_sv.allele_count
    assert in_sv.svuid == out_sv.svuid

    for in_allele, out_allele in zip(
            in_sv.alleles, out_sv.alleles, strict=True):
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
