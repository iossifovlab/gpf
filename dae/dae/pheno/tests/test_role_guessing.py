'''
Created on Jul 26, 2017

@author: lubo
'''
import pytest
import pandas as pd

from dae.pheno.prepare.ped_prepare import PreparePersons
from dae.variants.attributes import Role


@pytest.mark.skip('Disabling role guessing for now')
def test_role_guessing(test_config, sample_nuc_family):
    test_config.person.role.type = 'guess'
    prep = PreparePersons(test_config)

    ped_df = prep.load_pedigree_file(sample_nuc_family)
    assert ped_df is not None

    ped_df = prep._guess_role_nuc(ped_df)
    assert ped_df is not None
    assert 'role' in ped_df
    assert list(ped_df['role']) == [Role.dad, Role.mom, Role.prb, Role.sib]


def test_role_guessing_is_disabled(test_config, sample_nuc_family):
    test_config.person.role.type = 'guess'
    prep = PreparePersons(test_config)

    with pytest.raises(AssertionError):
        prep.load_pedigree_file(sample_nuc_family)

    with pytest.raises(AssertionError):
        prep._prepare_persons(pd.DataFrame())
