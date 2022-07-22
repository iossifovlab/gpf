# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.variants.attributes import Role


pytestmark = pytest.mark.xfail(reason="Wrappers don't exist anymore")


def test_genotype_data_group_with_phenodb_can_be_loaded(
    quads_f1_genotype_data_group_wrapper,
):
    assert quads_f1_genotype_data_group_wrapper is not None


def test_query_passes(quads_f1_genotype_data_group_wrapper):
    assert (
        len(list(quads_f1_genotype_data_group_wrapper.query_variants())) != 0
    )


def test_all_alleles_have_pheno_values(quads_f1_genotype_data_group_wrapper):
    for variant in quads_f1_genotype_data_group_wrapper.query_variants():
        for allele in variant.alt_alleles:
            assert allele["instrument1.continuous.prb"] is not None
            assert allele["instrument1.raw.prb"] is not None
            assert allele["instrument1.categorical.prb"] is not None
            assert allele["instrument1.ordinal.prb"] is not None
            assert allele["instrument1.categorical.mom"] is not None
            assert allele["instrument1.categorical.dad"] is not None
            assert allele["instrument1.categorical.dad"] != \
                allele["instrument1.categorical.mom"]


@pytest.mark.parametrize(
    "roles,column,value",
    [
        (str(Role.prb.name), "instrument1.continuous.prb", ["3.14"]),
        (str(Role.prb.name), "instrument1.categorical.prb", ["option2"]),
        (str(Role.prb.name), "instrument1.ordinal.prb", ["5.0"]),
        (str(Role.prb.name), "instrument1.raw.prb", ["somevalue"]),
        (str(Role.sib.name), "instrument1.continuous.sib", ["1.23", "4.56"]),
    ],
)
def test_alleles_have_pheno_values(
    roles, column, value, quads_f1_genotype_data_group_wrapper
):
    for variant in quads_f1_genotype_data_group_wrapper.query_variants(
        roles=roles
    ):
        assert len(variant.alt_alleles) > 0
        for allele in variant.alt_alleles:
            assert allele[column] == value
