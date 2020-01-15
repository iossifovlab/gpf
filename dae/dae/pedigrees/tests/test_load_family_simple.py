'''
Created on Jul 23, 2018

@author: lubo
'''
import os
import pytest
import pandas as pd

from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.family import FamiliesData

from .conftest import relative_to_this_folder


@pytest.mark.parametrize("fixture_name", [
    "fixtures/pedigrees/family_simple.txt"
])
def test_load_family_simple(fixture_name, temp_filename):
    family_filename = relative_to_this_folder(fixture_name)
    assert os.path.exists(family_filename)

    fam_df = FamiliesLoader.load_simple_family_file(family_filename)
    assert fam_df is not None
    print("-------------------------")
    print("-------------------------")
    print(fam_df)
    print("-------------------------")

    families = FamiliesData.from_pedigree_df(fam_df)

    assert families is not None

    FamiliesLoader.save_pedigree(fam_df, temp_filename)
    assert fam_df is not None

    ped_df = FamiliesLoader.flexible_pedigree_read(temp_filename)
    print("-------------------------")
    print("-------------------------")
    print(ped_df)
    print("-------------------------")

    pd.testing.assert_frame_equal(fam_df, ped_df)
