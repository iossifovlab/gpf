'''
Created on Jul 26, 2017

@author: lubo
'''
from __future__ import unicode_literals
from pheno.prepare.ped_prepare import PreparePersons
from variants.attributes import Role


def test_role_guessing(test_config, sample_nuc_family):
    test_config.person.role.type = 'guess'
    prep = PreparePersons(test_config)

    ped_df = prep.load_pedfile(sample_nuc_family)
    assert ped_df is not None

    ped_df = prep._guess_role_nuc(ped_df)
    assert ped_df is not None
    assert 'role' in ped_df
    assert list(ped_df['role']) == [Role.dad, Role.mom, Role.prb, Role.sib]
