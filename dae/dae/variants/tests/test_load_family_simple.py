'''
Created on Jul 23, 2018

@author: lubo
'''
import os
import pytest
import pandas as pd

from dae.pedigrees.pedigree_reader import PedigreeReader
from ..family import FamiliesBase, Family

from .conftests import relative_to_this_test_folder


@pytest.mark.parametrize("fixture_name", [
    "fixtures/family_simple.txt"
])
def test_load_family_simple(fixture_name, temp_filename):
    family_filename = relative_to_this_test_folder(fixture_name)
    assert os.path.exists(family_filename)

    fam_df = FamiliesBase.load_simple_family_file(family_filename)
    assert fam_df is not None
    print("-------------------------")
    print("-------------------------")
    print(fam_df)
    print("-------------------------")

    families = FamiliesBase(fam_df)
    families.families_build(fam_df, Family)

    assert families is not None

    PedigreeReader.save_pedigree(fam_df, temp_filename)
    assert fam_df is not None

    ped_df = PedigreeReader.load_pedigree_file(temp_filename)
    print("-------------------------")
    print("-------------------------")
    print(ped_df)
    print("-------------------------")

    pd.testing.assert_frame_equal(fam_df, ped_df)
