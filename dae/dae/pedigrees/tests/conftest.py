import pytest

import os
from io import StringIO
import csv

from dae.pedigrees.layout_saver import LayoutSaver
from dae.pedigrees.layout_loader import LayoutLoader
from dae.pedigrees.family import Family, FamiliesLoader

from dae.pedigrees.pedigrees import Individual, \
    FamilyConnections, MatingUnit, SibshipUnit
from dae.pedigrees.family import Person

from dae.pedigrees.interval_sandwich import SandwichSolver
from dae.pedigrees.layout import IndividualWithCoordinates, Layout
from dae.pedigrees.drawing import OffsetLayoutDrawer


def relative_to_this_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture(scope='session')
def input_filename():
    return relative_to_this_folder('fixtures/test.ped')


@pytest.fixture(scope='session')
def output_filename():
    return StringIO()


@pytest.fixture(scope='session')
def output():
    return StringIO()


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


@pytest.fixture(scope='function')
def member1(error_message):
    return Person(
        person_id='id1',
        family_id='fam1',
        mom_id='mom1',
        dad_id='dad1',
        sex='2',
        status='2',
        role='prb',
        layout=error_message,
        generated=False)


@pytest.fixture(scope='function')
def member2():
    return Person(
        person_id='mom1',
        family_id='fam1',
        mom_id='0',
        dad_id='0',
        sex='2',
        status='1',
        role='mom',
        layout=error_message,
        generated=False)


@pytest.fixture(scope='function')
def member3():
    return Person(
        person_id='dad1',
        family_id='fam1',
        mom_id='0',
        dad_id='0',
        sex='1',
        status='1',
        role='dad',
        layout=error_message,
        generated=True)


@pytest.fixture(scope='function')
def member4():
    return Person(
        person_id='id2',
        family_id='fam2',
        mom_id='mom2',
        dad_id='dad2',
        sex='1',
        status='2',
        role='prb',
        layout='2:100.0,75.0',
        generated=False)


@pytest.fixture(scope='function')
def member5():
    return Person(
        person_id='mom2',
        family_id='fam2',
        mom_id='0',
        dad_id='0',
        sex='2',
        status='1',
        role='mom',
        layout='1:50.0,50.0',
        generated=False)


@pytest.fixture(scope='function')
def member6():
    return Person(
        person_id='dad2',
        family_id='fam2',
        mom_id='0',
        dad_id='0',
        sex='1',
        status='1',
        role='dad',
        layout='1:50.0,100.0',
        generated=True)


@pytest.fixture(scope='function')
def member7():
    return Person(
        person_id='id3',
        family_id='fam3',
        mom_id='mom3',
        dad_id='0',
        sex='1',
        status='2',
        role='prb')


@pytest.fixture(scope='function')
def individual4(member4):
    return Individual(member=member4)


@pytest.fixture(scope='function')
def individual5(member5):
    return Individual(member=member5)


@pytest.fixture(scope='function')
def individual6(member6):
    return Individual(member=member6)


@pytest.fixture(scope='function')
def family1(member1, member2, member3):
    return Family.from_persons([member1, member2, member3])


@pytest.fixture(scope='function')
def family2(member4, member5, member6):
    return Family.from_persons([member4, member5, member6])


@pytest.fixture(scope='function')
def family3(member7):
    return Family.from_persons([member7])


@pytest.fixture(scope='function')
def sibship_unit2(individual4):
    return SibshipUnit({individual4})


@pytest.fixture(scope='function')
def mating_unit2(individual5, individual6, sibship_unit2):
    return MatingUnit(individual5, individual6, sibship_unit2)


@pytest.fixture(scope='function')
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


@pytest.fixture(scope='function')
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


@pytest.fixture(scope='function')
def people1(member1, member2, member3):
    return {
        'fam1;id1': member1,
        'fam1;mom1': member2,
        'fam1;dad1': member3
    }


@pytest.fixture(scope='function')
def people2(member4, member5, member6):
    return {
        'fam2;id2': member4,
        'fam2;mom2': member5,
        'fam2;dad2': member6
    }


@pytest.fixture(scope='function')
def layout2(individual4, individual5, individual6):
    layout = Layout()
    layout._id_to_position = {
        individual4: IndividualWithCoordinates(individual4, 100.0, 75.0),
        individual5: IndividualWithCoordinates(individual5, 50.0, 50.0),
        individual6: IndividualWithCoordinates(individual6, 50.0, 100.0)
    }
    layout._individuals_by_rank = [
        [individual5, individual6],
        [individual4]
    ]
    return layout


@pytest.fixture(scope='function')
def family_connections_from_family2(family2):
    return FamilyConnections.from_family(family2)


@pytest.fixture(scope='function')
def sandwich_instance_from_family2(family_connections_from_family2):
    return family_connections_from_family2.create_sandwich_instance()


@pytest.fixture(scope='function')
def intervals_from_family2(sandwich_instance_from_family2):
    return SandwichSolver.solve(sandwich_instance_from_family2)


@pytest.fixture(scope='function')
def individuals_intervals_from_family2(intervals_from_family2):
    return [interval for interval in intervals_from_family2
            if interval.vertex.is_individual()]


@pytest.fixture(scope='function')
def layout_from_family2(individuals_intervals_from_family2):
    return Layout(individuals_intervals_from_family2)


@pytest.fixture(scope='function')
def drawing_from_family2(layout_from_family2):
    return OffsetLayoutDrawer(
        layout_from_family2, 0, 0, show_id=True, show_family=True
    )


@pytest.fixture(scope='session')
def columns_labels():
    return {
        'family_id': 'familyId',
        'id': 'personId',
        'father': 'dadId',
        'mother': 'momId',
        'sex': 'sex',
        'status': 'status',
        'layout': 'layout',
        'role': 'role'
    }


@pytest.fixture(scope='session')
def header():
    return ['familyId', 'personId', 'dadId', 'momId', 'sex', 'status',
            'role']


@pytest.fixture(scope='session')
def dict_writer(output, header, layout_column, generated_column):
    dict_header = header + [layout_column, generated_column]
    return csv.DictWriter(
        output, dict_header, delimiter='\t',
        lineterminator='\n')


@pytest.fixture(scope='session')
def test_output():
    return """familyId\tpersonId\tdadId\tmomId\tsex\tstatus\trole\tlayout\tgenerated
fam1\tid1\tdad1\tmom1\t1\t2\tprb\tError\t
fam1\tmom1\t0\t0\t2\t1\tmom\tError\t
fam2\tid2\tdad2\tmom2\t1\t2\tprb\t2:100.0,75.0\t
fam2\tdad2\t0\t0\t1\t1\tdad\t1:50.0,100.0\t1
fam2\tmom2\t0\t0\t2\t1\tmom\t1:50.0,50.0\t
fam3\tid3\tdad3\tmom3\t2\t2\tprb\t\t
fam1\tdad1\t0\t0\t1\t1\tdad\tError\t1
"""


@pytest.fixture(scope='function')
def layout_loader1(family1):
    return LayoutLoader(family1)


@pytest.fixture(scope='function')
def layout_loader2(family2):
    return LayoutLoader(family2)


@pytest.fixture(scope='function')
def layout_positions2(member4, member5, member6):
    return [
        [IndividualWithCoordinates(Individual(member=member6), 50.0, 100.0),
         IndividualWithCoordinates(Individual(member=member5), 50.0, 50.0)],
        [IndividualWithCoordinates(Individual(member=member4), 100.0, 75.0)]
    ]


@pytest.fixture(scope='function')
def loaded_layout2(layout_positions2):
    layout = Layout()

    layout.positions = layout_positions2

    return layout


@pytest.fixture(scope='session')
def pedigree_test(input_filename):
    loader = FamiliesLoader(input_filename)
    families = loader.load()
    return families


@pytest.fixture(scope='session')
def fam1(pedigree_test):
    return pedigree_test['fam1']


@pytest.fixture(scope='session')
def fam1_family_connections(fam1):
    return FamilyConnections.from_family(fam1)


@pytest.fixture(scope='session')
def sample_nuc_family():
    return relative_to_this_folder('fixtures/sample_nuc_family.ped')
