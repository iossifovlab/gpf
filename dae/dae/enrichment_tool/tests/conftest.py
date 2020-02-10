import pytest

import os

from dae.enrichment_tool.background import CodingLenBackground, \
    SamochaBackground


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='session')
def local_gpf_instance(gpf_instance):
    return gpf_instance(fixtures_dir())


@pytest.fixture(scope='session')
def variants_db_fixture(local_gpf_instance):
    return local_gpf_instance._variants_db


@pytest.fixture(scope='session')
def f1_trio_enrichment_config(variants_db_fixture):
    return variants_db_fixture.get_config('f1_trio').enrichment


@pytest.fixture(scope='session')
def f1_trio(variants_db_fixture):
    result = variants_db_fixture.get('f1_trio')
    # for _, fvs in result._backend.full_variants:
    #     for fv in fvs:
    #         for fa in fv.alleles:
    #             inheritance_in_members = fa.inheritance_in_members
    #             inheritance_in_members = [
    #                 inh if inh != Inheritance.possible_denovo
    #                 else Inheritance.denovo
    #                 for inh in inheritance_in_members
    #             ]
    #             fa._inheritance_in_members = inheritance_in_members
    return result


@pytest.fixture(scope='session')
def f1_trio_coding_len_background(f1_trio_enrichment_config):
    return CodingLenBackground(f1_trio_enrichment_config)


@pytest.fixture(scope='session')
def f1_trio_samocha_background(f1_trio_enrichment_config):
    return SamochaBackground(f1_trio_enrichment_config)


@pytest.fixture(scope='session')
def background_facade(local_gpf_instance):
    return local_gpf_instance._background_facade
