import os
import pytest
from dae.pedigrees.pedigree_reader import PedigreeReader
from dae.pedigrees.family import FamiliesData


def relative_to_this_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture(scope='session')
def fake_families():
    ped_df = PedigreeReader.load_pedigree_file(
        relative_to_this_folder(
            'fixtures/fake_pheno.ped'
        )
    )
    fake_families = FamiliesData.from_pedigree_df(ped_df)
    return fake_families
