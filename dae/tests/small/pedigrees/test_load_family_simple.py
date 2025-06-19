# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
from collections.abc import Callable

import pytest
from dae.pedigrees.loader import FamiliesLoader


@pytest.mark.parametrize("fixture_name", ["pedigrees/family_simple.txt"])
def test_load_family_simple(
    fixture_name: str, tmp_path: pathlib.Path,
    fixture_dirname: Callable,
) -> None:
    family_filename = fixture_dirname(fixture_name)
    assert os.path.exists(family_filename)

    families = FamiliesLoader.load_simple_families_file(family_filename)
    assert families is not None

    FamiliesLoader.save_pedigree(families, str(tmp_path / "temp.ped"))

    families1 = FamiliesLoader.load_pedigree_file(str(tmp_path / "temp.ped"))

    assert set(families.keys()) == set(families1.keys())
