import os
import pytest
from tools.denovo2DAE import parse_cli_arguments, denovo2DAE, export
from tools.tests.test_denovo2DAE import path
from DAE import pheno
from tools.tests.fixtures.pheno_data import DB, DBS, populate_instruments


FAMILIES_COLUMNS = ['--familyId=familyId', '--sex=gender',
                    '--momId=momId', '--dadId=dadId']

@pytest.fixture(scope='session')
def dae():
    args = [path('dnv2dae/vs.tsv'), path('dnv2dae/fs.ped')] + FAMILIES_COLUMNS
    return denovo2DAE(parse_cli_arguments(args))


@pytest.fixture(scope='session')
def dae_file(dae, request):
    out = path('dnv2dae/out.tsv')
    export(out, dae)
    request.addfinalizer(lambda: os.remove(out))
    return out


@pytest.fixture(scope='session')
def dae_with_columns():
    args = [path('dnv2dae/yuen_subset_cols.csv'),
            path('dnv2dae/yuen_families.ped'), '-si=SAMPLE',
            '-c=CHROM', '-p=START', '-r=REF', '-a=ALT'] + FAMILIES_COLUMNS
    return denovo2DAE(parse_cli_arguments(args))


@pytest.fixture(scope='session')
def dae_xlsx():
    args = [path('dnv2dae/yuen_subset.xlsx'),
            path('dnv2dae/yuen_families.ped')] + FAMILIES_COLUMNS
    return denovo2DAE(parse_cli_arguments(args))


@pytest.fixture(scope='session')
def dae_zero_based():
    args = [path('dnv2dae/yuen_subset.csv'), path('dnv2dae/yuen_families.ped')]
    return denovo2DAE(parse_cli_arguments(args)), \
        denovo2DAE(parse_cli_arguments(args + ['--zerobased']))


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
