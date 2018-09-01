import pytest
from DAE import pheno
from fixtures.pheno_data import populate_instruments, DB, DBS


@pytest.fixture()
def db(mocker):
    instruments, measures = populate_instruments()

    mocker.patch.object(pheno, 'get_pheno_db_names')
    pheno.get_pheno_db_names.return_value = DBS
    mocker.patch.object(pheno, 'get_pheno_db')
    pheno.get_pheno_db(DB).instruments = instruments
    pheno.get_pheno_db(DB).measures = measures

    return mocker


@pytest.fixture(params=['i1.m1', 'i2.m3,i1.m1'],
                ids=['MeasureIds', 'MultipleMeasureIds'])
def measure_ids_filter(request):
    return request.param


@pytest.fixture(params=[('ordinal', ['i2.m3', 'i2.m4', 'i2.m5']),
                        ('ordinal,continuous',
                         ['i1.m1', 'i2.m3', 'i2.m4', 'i2.m5'])],
                ids=['MeasureTypes', 'MultipleMeasureTypes'])
def measure_types_filter(request):
    return request.param


@pytest.fixture(params=[('i1', ['i1.m1', 'i1.m2']),
                        ('i1,i3',
                         ['i1.m1', 'i1.m2', 'i3.m6', 'i3.m1'])],
                ids=['InstrumentIds', 'MultipleInstrumentIds'])
def instrument_ids_filter(request):
    return request.param


@pytest.fixture(params=[(['--instrumentIds=i2', '--measureTypes=ordinal',
                          '--measureIds=i2.m3,i1.m1'],
                         ['i2.m3']),
                        (['--measureTypes=categorical', '--instrumentIds=i2'],
                         [])],
                ids=['complex: instrumentId:i2, type:ordinal, ids:i2.m3,i1.m1',
                     'complex: instrumentId:i2, type:categorical'])
def complex_measures_filter(request):
    return request.param
