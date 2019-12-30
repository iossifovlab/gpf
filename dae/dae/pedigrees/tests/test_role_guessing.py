'''
Created on Jul 26, 2017

@author: lubo
'''
from dae.pedigrees.family import FamiliesLoader, PedigreeRoleGuesser
from dae.variants.attributes import Role


def test_role_guessing(sample_nuc_family):
    ped_df_copy = FamiliesLoader.flexible_pedigree_read(sample_nuc_family)
    ped_df = FamiliesLoader.flexible_pedigree_read(sample_nuc_family)
    assert ped_df is not None

    res_df = PedigreeRoleGuesser.guess_role_nuc(ped_df)
    assert res_df is not None
    assert 'role' in res_df
    assert list(res_df['role']) == [Role.dad, Role.mom, Role.prb, Role.sib]

    # Assert lack of side effects
    assert 'role' not in ped_df  # Check for side-effects
    assert ped_df.equals(ped_df_copy)
