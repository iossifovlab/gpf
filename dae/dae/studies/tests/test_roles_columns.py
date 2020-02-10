def test_all_in_role_columns_are_present_in_config(
        quads_f1_genotype_data_group_wrapper):
    in_role_cols = quads_f1_genotype_data_group_wrapper.\
        config.genotype_browser_config.in_role_columns

    assert in_role_cols
    in_role_cols_ids = [role.id for role in in_role_cols]

    assert in_role_cols_ids == ['inChild', 'fromParent']


def test_alleles_have_roles_columns(quads_f1_genotype_data_group_wrapper):
    variants = list(quads_f1_genotype_data_group_wrapper.query_variants())

    assert len(variants) == 3

    for variant in variants:
        for alt_allele in variant.alt_alleles:
            print(alt_allele.attributes)
            assert alt_allele.get_attribute('inChS') is not None
            assert alt_allele.get_attribute('fromParentS') is not None


def test_chr1_variant_has_corrent_roles_values(
        quads_f1_genotype_data_group_wrapper):
    variants = list(quads_f1_genotype_data_group_wrapper.query_variants(
        regions=["1:0-999999999999999"]))

    assert len(variants) == 1
    variant = variants[0]

    assert len(variant.alt_alleles) == 1
    allele = variant.alt_alleles[0]

    assert allele.get_attribute('inChS') == 'prbM'
    assert allele.get_attribute('fromParentS') == 'momF'


def test_chr2_variant_has_corrent_roles_values(
        quads_f1_genotype_data_group_wrapper):
    variants = list(quads_f1_genotype_data_group_wrapper.query_variants(
        regions=["2:0-999999999999999"]))

    assert len(variants) == 1
    variant = variants[0]

    assert len(variant.alt_alleles) == 1
    allele = variant.alt_alleles[0]

    assert allele.get_attribute('inChS') == 'prbM'
    assert allele.get_attribute('fromParentS') == 'dadM'


def test_chr3_variant_has_both_siblings(quads_f1_genotype_data_group_wrapper):
    variants = list(quads_f1_genotype_data_group_wrapper.query_variants(
        regions=["3:0-999999999999999"]))

    assert len(variants) == 1
    variant = variants[0]

    assert len(variant.alt_alleles) == 1
    allele = variant.alt_alleles[0]

    assert allele.get_attribute('inChS') == 'sibFsibF'
    assert allele.get_attribute('fromParentS') == 'dadM'
