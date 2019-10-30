'''
Created on Jul 26, 2017

@author: lubo
'''
from dae.pedigrees.pedigree_reader import PedigreeReader, PedigreeRoleGuesser
from dae.variants.attributes import Role


def test_role_guessing(sample_nuc_family):
    ped_df = PedigreeReader.load_pedigree_file(sample_nuc_family)
    assert ped_df is not None

    ped_df = PedigreeRoleGuesser.guess_role_nuc(ped_df)
    assert ped_df is not None
    assert 'role' in ped_df
    assert list(ped_df['role']) == [Role.dad, Role.mom, Role.prb, Role.sib]
