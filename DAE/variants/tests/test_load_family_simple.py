'''
Created on Jul 23, 2018

@author: lubo
'''
import os

import pytest

from variants.tests.common_tests_helpers import relative_to_this_test_folder
from variants.family import FamiliesBase


@pytest.mark.parametrize("fixture_name", [
    "fixtures/family_simple.txt"
])
def test_load_family_simple(fixture_name):
    family_filename = relative_to_this_test_folder(fixture_name)
    assert os.path.exists(family_filename)

    fam_df = FamiliesBase.load_simple_family_file(family_filename)
    assert fam_df is not None
    print(fam_df.head())
