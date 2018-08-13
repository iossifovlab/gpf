'''
Created on Jul 23, 2018

@author: lubo
'''
import os

import pytest

from variants.tests.common_tests_helpers import relative_to_this_test_folder
from variants.family import FamiliesBase, Family


@pytest.mark.parametrize("fixture_name", [
    "fixtures/family_simple.txt"
])
def test_load_family_simple(fixture_name):
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


@pytest.mark.parametrize("fixture_name", [
    "fixtures/family_simple.txt",
])
def test_family_simple_index(fixture_name):
    family_filename = relative_to_this_test_folder(fixture_name)
    assert os.path.exists(family_filename)

    ped_df = FamiliesBase.load_simple_family_file(family_filename)

    unique_family_index = ped_df['familyIndex'].unique()
    print(unique_family_index)

    for findex in unique_family_index:
        fids = ped_df[ped_df['familyIndex'] == findex]['familyId'].unique()
        print(fids)
        assert len(fids) == 1
