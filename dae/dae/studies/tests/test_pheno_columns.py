import pytest
from dae.variants.attributes import Role


def test_dataset_with_phenodb_can_be_loaded(quads_f1_dataset_wrapper):
    assert quads_f1_dataset_wrapper is not None


def test_query_passes(quads_f1_dataset_wrapper):
    assert len(list(quads_f1_dataset_wrapper.query_variants())) != 0


def test_all_alleles_have_pheno_values(quads_f1_dataset_wrapper):
    for variant in quads_f1_dataset_wrapper.query_variants():
        for allele in variant.alt_alleles:
            assert allele["prb.instrument1.continuous"] is not None
            assert allele["prb.instrument1.raw"] is not None
            assert allele["prb.instrument1.categorical"] is not None
            assert allele["prb.instrument1.ordinal"] is not None


@pytest.mark.parametrize("roles,column,value", [
    (str(Role.prb.name), "prb.instrument1.continuous", '3.14'),
    (str(Role.prb.name), "prb.instrument1.categorical", 'option2'),
    (str(Role.prb.name), "prb.instrument1.ordinal", '5.0'),
    (str(Role.prb.name), "prb.instrument1.raw", 'somevalue'),
])
def test_alleles_have_pheno_values(
        roles, column, value, quads_f1_dataset_wrapper):
    for variant in quads_f1_dataset_wrapper.query_variants(roles=roles):
        assert len(variant.alt_alleles) > 0
        for allele in variant.alt_alleles:
            assert allele[column] == value
