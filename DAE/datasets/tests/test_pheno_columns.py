from builtins import str

import pytest
from variants.attributes import Role

pytestmark = pytest.mark.usefixtures("pheno_conf_path")


def test_dataset_with_phenodb_can_be_loaded(quads_f1_wrapper):
    assert quads_f1_wrapper is not None


def test_query_passes(quads_f1_wrapper):
    assert len(list(quads_f1_wrapper.get_variants())) != 0


def test_all_alleles_have_pheno_values(quads_f1_wrapper):
    for variant in quads_f1_wrapper.get_variants():
        for allele in variant.matched_alleles:
            assert allele["Continuous"]
            assert allele["Raw"]
            assert allele["Categorical"]
            assert allele["Ordinal"]


@pytest.mark.parametrize("roles,type,value", [
    (str(Role.prb.name), "Continuous", '3.14'),
    (str(Role.prb.name), "Categorical", 'option2'),
    (str(Role.prb.name), "Ordinal", '5.0'),
    (str(Role.prb.name), "Raw", 'somevalue'),
])
def test_alleles_have_pheno_values(roles, type, value, quads_f1_wrapper):
    for variant in quads_f1_wrapper.get_variants(roles=roles):
        assert len(variant.matched_alleles) > 0
        for allele in variant.matched_alleles:
            assert allele[type] is not None
            assert allele[type] == value
