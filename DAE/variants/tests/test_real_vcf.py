'''
Created on Mar 5, 2018

@author: lubo
'''
from variants.variant import mat2str
import pytest


def slow():
    pytest.mark.skipif(
        not pytest.config.getoption("--runslow"),  # @UndefinedVariable
        reason="need --runslow option to run"
    )


def test_nvcf_config(nvcf_config):
    print(nvcf_config)
    assert nvcf_config is not None


def test_nvcf_all_variants(nvcf):
    assert nvcf is not None

    for v in nvcf.query_variants():
        print(v, v.family_id, mat2str(v.best_st), v.inheritance)


@pytest.mark.slow
def test_uvcf_all_variants(uvcf):
    for v in uvcf.query_variants():
        print(v, v.family_id, mat2str(v.best_st), v.inheritance)


@pytest.mark.veryslow
def test_fvcf_all_variants(fvcf):
    for v in fvcf.query_variants():
        print(v, v.family_id, mat2str(v.best_st), v.inheritance)
