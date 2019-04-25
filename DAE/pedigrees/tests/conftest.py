import pytest

from io import StringIO
import six
import csv

from pedigrees.layout_saver import LayoutSaver
from pedigrees.layout_loader import LayoutLoader
from pedigrees.pedigree_reader import PedigreeReader
from pedigrees.pedigrees import Pedigree, PedigreeMember, Individual, \
    FamilyConnections
from pedigrees.layout import IndividualWithCoordinates, Layout
from utils.fixtures import path_to_fixtures as _path_to_fixtures


def path_to_fixtures(*args):
    return _path_to_fixtures('pedigrees', *args)


@pytest.fixture(scope='session')
def input_filename():
    return path_to_fixtures('input', 'test.ped')


@pytest.fixture(scope='session')
def output_filename():
    return StringIO()


@pytest.fixture(scope='session')
def output():
    return six.StringIO()


@pytest.fixture(scope='session')
def generated_column():
    return 'generated'


@pytest.fixture(scope='session')
def layout_column():
    return 'layout'


@pytest.fixture
def layout_saver(
        input_filename, output_filename, generated_column, layout_column):
    return LayoutSaver(
        input_filename, output_filename, generated_column, layout_column)


@pytest.fixture(scope='session')
def error_message():
    return 'Error'


@pytest.fixture(scope='session')
def member1(error_message):
    return PedigreeMember(
        'id1', 'fam1', 'mom1', 'dad1', '1', '2', 'prb', error_message, False)


@pytest.fixture(scope='session')
def member2():
    return PedigreeMember(
        'mom1', 'fam1', '0', '0', '2', '1', 'mom', error_message, False)


@pytest.fixture(scope='session')
def member3():
    return PedigreeMember(
        'dad1', 'fam1', '0', '0', '1', '1', 'dad', error_message, True)


@pytest.fixture(scope='session')
def member4():
    return PedigreeMember(
        'id2', 'fam2', 'mom2', 'dad2', '1', '2', 'prb', '2:100.0,75.0', False)


@pytest.fixture(scope='session')
def member5():
    return PedigreeMember(
        'mom2', 'fam2', '0', '0', '2', '1', 'mom', '1:50.0,50.0', False)


@pytest.fixture(scope='session')
def member6():
    return PedigreeMember(
        'dad2', 'fam2', '0', '0', '1', '1', 'dad', '1:50.0,100.0', True)


@pytest.fixture(scope='session')
def family1(member1, member2, member3):
    return Pedigree([member1, member2, member3])


@pytest.fixture(scope='session')
def family2(member4, member5, member6):
    return Pedigree([member4, member5, member6])


@pytest.fixture(scope='session')
def people_with_layout_error(layout_column, generated_column, error_message):
    return {
        'fam1;id1': {
            layout_column: error_message,
            generated_column: ''
        },
        'fam1;mom1': {
            layout_column: error_message,
            generated_column: ''
        },
        'fam1;dad1': {
            layout_column: error_message,
            generated_column: '1'
        }
    }


@pytest.fixture(scope='session')
def people_with_layout(
        layout_column, generated_column, member4, member5, member6):
    return {
        'fam2;id2': {
            layout_column: member4.layout,
            generated_column: ''
        },
        'fam2;mom2': {
            layout_column: member5.layout,
            generated_column: ''
        },
        'fam2;dad2': {
            layout_column: member6.layout,
            generated_column: '1'
        }
    }


@pytest.fixture(scope='session')
def people1(member1, member2, member3):
    return {
        'fam1;id1': member1,
        'fam1;mom1': member2,
        'fam1;dad1': member3
    }


@pytest.fixture(scope='session')
def people2(member4, member5, member6):
    return {
        'fam2;id2': member4,
        'fam2;mom2': member5,
        'fam2;dad2': member6
    }


@pytest.fixture(scope='session')
def layout2(member4, member5, member6):
    layout = Layout()
    layout._id_to_position = {
        Individual(member=member4): IndividualWithCoordinates(
            Individual(member=member4), 100.0, 75.0),
        Individual(member=member5): IndividualWithCoordinates(
            Individual(member=member5), 50.0, 50.0),
        Individual(member=member6): IndividualWithCoordinates(
            Individual(member=member6), 50.0, 100.0)
    }
    layout._individuals_by_rank = [
        [Individual(member=member5), Individual(member=member6)],
        [Individual(member=member4)]]
    return layout


@pytest.fixture(scope='session')
def columns_labels():
    return {
        'family_id': 'familyId',
        'id': 'personId',
        'father': 'dadId',
        'mother': 'momId',
        'sex': 'gender',
        'status': 'status',
        'layout': 'layout',
        'role': 'role'
    }


@pytest.fixture(scope='session')
def header():
    return ['familyId', 'personId', 'dadId', 'momId', 'gender', 'status',
            'role']


@pytest.fixture(scope='session')
def dict_writer(output, header, layout_column, generated_column):
    dict_header = header + [layout_column, generated_column]
    return csv.DictWriter(
        output, dict_header, delimiter='\t',
        lineterminator='\n')


@pytest.fixture(scope='session')
def test_output():
    return """familyId\tpersonId\tdadId\tmomId\tgender\tstatus\trole\tlayout\tgenerated
fam1\tid1\tdad1\tmom1\t1\t2\tprb\tError\t
fam1\tmom1\t0\t0\t2\t1\tmom\tError\t
fam2\tid2\tdad2\tmom2\t1\t2\tprb\t2:100.0,75.0\t
fam2\tdad2\t0\t0\t1\t1\tdad\t1:50.0,100.0\t1
fam2\tmom2\t0\t0\t2\t1\tmom\t1:50.0,50.0\t
fam3\tid3\tdad3\tmom3\t2\t2\tprb\t\t
fam1\tdad1\t0\t0\t1\t1\tdad\tError\t1
"""


@pytest.fixture
def layout_loader1(family1):
    return LayoutLoader(family1)


@pytest.fixture
def layout_loader2(family2):
    return LayoutLoader(family2)


@pytest.fixture(scope='session')
def layout_positions2(member4, member5, member6):
    return [
        [IndividualWithCoordinates(Individual(member=member6), 50.0, 100.0),
         IndividualWithCoordinates(Individual(member=member5), 50.0, 50.0)],
        [IndividualWithCoordinates(Individual(member=member4), 100.0, 75.0)]
    ]


@pytest.fixture(scope='session')
def loaded_layout2(layout_positions2):
    layout = Layout()

    layout.positions = layout_positions2

    return layout


@pytest.fixture(scope='session')
def pedigree_reader():
    return PedigreeReader()


@pytest.fixture(scope='session')
def pedigree_test(pedigree_reader, input_filename):
    return pedigree_reader.read_file(input_filename, return_as_dict=True)


@pytest.fixture(scope='session')
def fam1(pedigree_test):
    return pedigree_test['fam1']


@pytest.fixture(scope='session')
def fam1_family_connections(fam1):
    return FamilyConnections.from_pedigree(fam1)

