from __future__ import print_function
from __future__ import unicode_literals

import pytest

from io import StringIO
import pandas as pd

from variants.family import FamiliesBase
from variants.attributes import Role, Sex, Status


@pytest.mark.parametrize("infile,pedigree", [
    (StringIO("""
familyId\tpersonId\tdadId\tmomId\tsex\tstatus\trole\tlayout
1\t1.x1\t0\t0\t2\t1\tmom\t1:53.5,50.0
1\t1.x2\t0\t0\t1\t1\tdad\t1:10.0,50.0
1\t1.x3\t1.x2\t1.x1\t2\t2\tprb\t2:31.75,80.0
"""), pd.DataFrame({
        'familyId': ['1', '1', '1'],
        'personId': ['1.x1', '1.x2', '1.x3'],
        'dadId': ['0', '0', '1.x2'],
        'momId': ['0', '0', '1.x1'],
        'sex': [Sex.female, Sex.male, Sex.female],
        'status': [Status.unaffected, Status.unaffected, Status.affected],
        'role': [Role.mom, Role.dad, Role.prb],
        'layout': ['53.5,50.0', '10.0,50.0', '31.75,80.0'],
        'sampleId': ['1.x1', '1.x2', '1.x3']
    })),
    (StringIO("""
familyId\tpersonId\tdadId\tmomId\tgender\tstatus\trole\tlayout\tsampleId
1\t1.x1\t0\t0\t2\t1\tmom\t1:53.5,50.0\t1.x1
1\t1.x2\t0\t0\t1\t1\tdad\t1:10.0,50.0\t1.x2
1\t1.x3\t1.x2\t1.x1\t2\t2\tprb\t2:31.75,80.0\t1.x3
"""), pd.DataFrame({
        'familyId': ['1', '1', '1'],
        'personId': ['1.x1', '1.x2', '1.x3'],
        'dadId': ['0', '0', '1.x2'],
        'momId': ['0', '0', '1.x1'],
        'sex': [Sex.female, Sex.male, Sex.female],
        'status': [Status.unaffected, Status.unaffected, Status.affected],
        'role': [Role.mom, Role.dad, Role.prb],
        'layout': ['53.5,50.0', '10.0,50.0', '31.75,80.0'],
        'sampleId': ['1.x1', '1.x2', '1.x3']
    })),
    (StringIO("""
familyId\tpersonId\tdadId\tmomId\tsex\tstatus\trole\tlayout\tsampleId
1\t1.x1\t0\t0\t2\t1\tmom\t1:53.5,50.0\t
1\t1.x2\t0\t0\t1\t1\tdad\t1:10.0,50.0\t1.x2
1\t1.x3\t1.x2\t1.x1\t2\t2\tprb\t2:31.75,80.0\t
"""), pd.DataFrame({
        'familyId': ['1', '1', '1'],
        'personId': ['1.x1', '1.x2', '1.x3'],
        'dadId': ['0', '0', '1.x2'],
        'momId': ['0', '0', '1.x1'],
        'sex': [Sex.female, Sex.male, Sex.female],
        'status': [Status.unaffected, Status.unaffected, Status.affected],
        'role': [Role.mom, Role.dad, Role.prb],
        'layout': ['53.5,50.0', '10.0,50.0', '31.75,80.0'],
        'sampleId': ['1.x1', '1.x2', '1.x3']
    })),
])
def test_load_pedigree_file(infile, pedigree):
    loaded_pedigree = FamiliesBase.load_pedigree_file(infile, sep='\t')
    columns = ['familyId', 'personId', 'dadId', 'momId', 'sex', 'status',
               'role', 'layout', 'sampleId']
    for column in columns:
        assert (loaded_pedigree[column].values ==
                pedigree[column].values).all()
