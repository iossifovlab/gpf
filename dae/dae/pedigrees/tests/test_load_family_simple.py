import os
import pytest

from dae.pedigrees.loader import FamiliesLoader


@pytest.mark.parametrize("fixture_name", ["pedigrees/family_simple.txt"])
def test_load_family_simple(fixture_name, temp_filename, fixture_dirname):
    family_filename = fixture_dirname(fixture_name)
    assert os.path.exists(family_filename)

    families = FamiliesLoader.load_simple_families_file(family_filename)
    assert families is not None

    FamiliesLoader.save_pedigree(families, temp_filename)

    families1 = FamiliesLoader.load_pedigree_file(temp_filename)

    assert set(families.keys()) == set(families1.keys())
