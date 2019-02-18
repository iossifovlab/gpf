from builtins import str

import pytest
from variants.attributes import Role

pytestmark = pytest.mark.usefixtures("pheno_conf_path")


def test_dataset_with_phenodb_can_be_loaded(quads_f1_dataset_wrapper):
    assert quads_f1_dataset_wrapper is not None


def test_query_passes(quads_f1_dataset_wrapper):
    assert len(list(quads_f1_dataset_wrapper.query_variants())) != 0


def test_all_alleles_have_pheno_values(quads_f1_dataset_wrapper):
    for variant in quads_f1_dataset_wrapper.query_variants():
        for allele in variant.matched_alleles:
            assert allele["prb.instrument1.continuous"]
            assert allele["prb.instrument1.raw"]
            assert allele["prb.instrument1.categorical"]
            assert allele["prb.instrument1.ordinal"]


@pytest.mark.parametrize("roles,column,value", [
    (str(Role.prb.name), "prb.instrument1.continuous", '3.14'),
    (str(Role.prb.name), "prb.instrument1.categorical", 'option2'),
    (str(Role.prb.name), "prb.instrument1.ordinal", '5.0'),
    (str(Role.prb.name), "prb.instrument1.raw", 'somevalue'),
])
def test_alleles_have_pheno_values(
        roles, column, value, quads_f1_dataset_wrapper):
    for variant in quads_f1_dataset_wrapper.query_variants(roles=roles):
        assert len(variant.matched_alleles) > 0
        for allele in variant.matched_alleles:
            assert allele[column] == value
