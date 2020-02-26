def test_summary_sharing(variants_impl):
    fvars = variants_impl("variants_vcf")("backends/quads_two_families")

    assert fvars is not None

    full_variants = list(fvars.full_variants_iterator())

    assert id(full_variants[0][0]) == id(
        full_variants[0][1][0].summary_variant
    )
    assert id(full_variants[0][0]) == id(
        full_variants[0][1][0].summary_variant
    )
    assert id(full_variants[1][0]) == id(
        full_variants[1][1][0].summary_variant
    )
    assert id(full_variants[1][0]) == id(
        full_variants[1][1][0].summary_variant
    )

    full_alleles = list()
    for sv, fvs in full_variants:
        summary_alleles = sv.alleles
        family_alleles = list()
        for fv in fvs:
            family_alleles.append(fv.alleles)
        full_alleles.append((summary_alleles, family_alleles))

    assert id(full_alleles[0][0][0]) == id(
        full_alleles[0][1][0][0].summary_allele
    )
    assert id(full_alleles[0][0][1]) == id(
        full_alleles[0][1][0][1].summary_allele
    )
    assert id(full_alleles[0][0][0]) == id(
        full_alleles[0][1][1][0].summary_allele
    )
    assert id(full_alleles[1][0][0]) == id(
        full_alleles[1][1][0][0].summary_allele
    )
    assert id(full_alleles[1][0][0]) == id(
        full_alleles[1][1][1][0].summary_allele
    )
    assert id(full_alleles[1][0][1]) == id(
        full_alleles[1][1][1][1].summary_allele
    )
