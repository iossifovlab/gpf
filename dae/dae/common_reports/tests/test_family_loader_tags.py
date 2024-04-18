# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

from dae.pedigrees.loader import FamiliesLoader

from .conftest import fixtures_dir


def test_load_pedigree() -> None:

    ped_filename = os.path.join(
        fixtures_dir(),
        "studies/Study1/data/Study1.ped")

    families = FamiliesLoader.load_pedigree_file(ped_filename)

    assert families is not None

    assert len(families) == 10
