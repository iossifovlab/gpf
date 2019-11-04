import pytest
import pandas as pd

from dae.variants.attributes import Sex, Status, Role
from dae.pedigrees.pedigree_reader import PedigreeReader
from dae.pedigrees.tests.conftest import relative_to_this_folder


expected_pedigree_df = pd.DataFrame([
    ['f1', 'f1.dad', '0', '0', Sex.M, Status.unaffected, Role.dad],
    ['f1', 'f1.mom', '0', '0', Sex.F, Status.unaffected, Role.mom],
    ['f1', 'f1.s1', 'f1.dad', 'f1.mom', Sex.F, Status.unaffected, Role.sib],
    ['f1', 'f1.p1', 'f1.dad', 'f1.mom', Sex.M, Status.affected, Role.prb],
    ['f1', 'f1.s2', 'f1.dad', 'f1.mom', Sex.F, Status.affected, Role.sib],
    ['f2', 'f2.mom', '0', '0', Sex.F, Status.unaffected, Role.mom],
    ['f2', 'f2.dad', '0', '0', Sex.M, Status.unaffected, Role.dad],
    ['f2', 'f2.p1', 'f2.dad', 'f2.mom', Sex.M, Status.affected, Role.prb],
    ['f2', 'f2.s1', 'f2.dad', 'f2.mom', Sex.F, Status.unaffected, Role.sib],
], columns=['family_id',
            'person_id',
            'dad_id',
            'mom_id',
            'sex',
            'status',
            'role'],
)


@pytest.mark.parametrize('filepath', [
    ('pedigree_A.ped'),
    ('pedigree_B.ped'),
    ('pedigree_B2.ped'),
    ('pedigree_C.ped'),
])
def test_load_pedigree_file(filepath):
    expected_df = expected_pedigree_df.copy()
    expected_df['sample_id'] = expected_df['person_id']

    absolute_filepath = relative_to_this_folder(
        'fixtures/{}'.format(filepath)
    )
    pedigree_df = PedigreeReader.load_pedigree_file(absolute_filepath)
    assert pedigree_df.equals(expected_df)


def test_load_pedigree_file_additional_columns():
    expected_df = expected_pedigree_df.copy()
    expected_df['phenotype'] = [
        'healthy',
        'healthy',
        'healthy',
        'disease',
        'disease',
        'healthy',
        'healthy',
        'disease',
        'healthy',
    ]
    expected_df['sample_id'] = expected_df['person_id']

    absolute_filepath = relative_to_this_folder(
        'fixtures/pedigree_D.ped'
    )
    pedigree_df = PedigreeReader.load_pedigree_file(absolute_filepath)
    assert pedigree_df.equals(expected_df)


def test_load_pedigree_file_do_not_override_sample_id_column():
    expected_df = expected_pedigree_df.copy()
    expected_df['sample_id'] = [
        'f1_father',
        'f1_mother',
        'f1_sibling1',
        'f1_proband',
        'f1_sibling2',
        'f2_mother',
        'f2_father',
        'f2_proband',
        'f2_sibling1',
    ]

    absolute_filepath = relative_to_this_folder(
        'fixtures/pedigree_E.ped'
    )
    pedigree_df = PedigreeReader.load_pedigree_file(absolute_filepath)
    assert pedigree_df.equals(expected_df)
