import pytest
from io import StringIO
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


@pytest.mark.parametrize("infile,pedigree", [
    (StringIO("""
familyId\tpersonId\tdadId\tmomId\tsex\tstatus\trole\tlayout
1\t1.x1\t0\t0\t2\t1\tmom\t1:53.5,50.0
1\t1.x2\t0\t0\t1\t1\tdad\t1:10.0,50.0
1\t1.x3\t1.x2\t1.x1\t2\t2\tprb\t2:31.75,80.0
"""), pd.DataFrame({
        'family_id': ['1', '1', '1'],
        'person_id': ['1.x1', '1.x2', '1.x3'],
        'dad_id': ['0', '0', '1.x2'],
        'mom_id': ['0', '0', '1.x1'],
        'sex': [Sex.female, Sex.male, Sex.female],
        'status': [Status.unaffected, Status.unaffected, Status.affected],
        'role': [Role.mom, Role.dad, Role.prb],
        'layout': ['53.5,50.0', '10.0,50.0', '31.75,80.0'],
        'sample_id': ['1.x1', '1.x2', '1.x3']
    })),
    (StringIO("""
familyId\tpersonId\tdadId\tmomId\tsex\tstatus\trole\tlayout\tsampleId
1\t1.x1\t0\t0\t2\t1\tmom\t1:53.5,50.0\t
1\t1.x2\t0\t0\t1\t1\tdad\t1:10.0,50.0\t1.x2
1\t1.x3\t1.x2\t1.x1\t2\t2\tprb\t2:31.75,80.0\t
"""), pd.DataFrame({
        'family_id': ['1', '1', '1'],
        'person_id': ['1.x1', '1.x2', '1.x3'],
        'dad_id': ['0', '0', '1.x2'],
        'mom_id': ['0', '0', '1.x1'],
        'sex': [Sex.female, Sex.male, Sex.female],
        'status': [Status.unaffected, Status.unaffected, Status.affected],
        'role': [Role.mom, Role.dad, Role.prb],
        'layout': ['53.5,50.0', '10.0,50.0', '31.75,80.0'],
        'sample_id': ['1.x1', '1.x2', '1.x3']
    })),
])
def test_flexible_pedigree_read(infile, pedigree):
    loaded_pedigree = PedigreeReader.flexible_pedigree_read(infile, sep='\t')
    print(loaded_pedigree)
    columns = ['family_id', 'person_id', 'dad_id', 'mom_id', 'sex', 'status',
               'role', 'layout', 'sample_id']
    for column in columns:
        assert (loaded_pedigree[column].values ==
                pedigree[column].values).all()


@pytest.mark.parametrize('filepath', [
    ('pedigree_A.ped'),
    ('pedigree_B.ped'),
    ('pedigree_B2.ped'),
    ('pedigree_C.ped'),
])
def test_flexible_pedigree_read_from_filesystem(filepath):
    expected_df = expected_pedigree_df.copy()
    expected_df['sample_id'] = expected_df['person_id']

    absolute_filepath = relative_to_this_folder(
        'fixtures/{}'.format(filepath)
    )
    pedigree_df = PedigreeReader.flexible_pedigree_read(absolute_filepath)
    assert pedigree_df.equals(expected_df)


def test_flexible_pedigree_read_additional_columns():
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
    pedigree_df = PedigreeReader.flexible_pedigree_read(absolute_filepath)
    assert pedigree_df.equals(expected_df)


def test_flexible_pedigree_read_do_not_override_sample_id_column():
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
    pedigree_df = PedigreeReader.flexible_pedigree_read(absolute_filepath)
    assert pedigree_df.equals(expected_df)


def test_flexible_pedigree_read_no_header():
    expected_df = expected_pedigree_df.copy()
    expected_df['sample_id'] = expected_df['person_id']

    absolute_filepath = relative_to_this_folder(
        'fixtures/pedigree_no_header.ped'
    )
    pedigree_df = PedigreeReader.flexible_pedigree_read(
        absolute_filepath,
        has_header=False,
        col_family=0,
        col_person=1,
        col_dad=2,
        col_mom=3,
        col_sex=4,
        col_status=5,
        col_role=6,
    )
    print(pedigree_df)
    print(expected_df)
    assert pedigree_df.equals(expected_df)
