import os
import pytest
from tools.denovo2DAE import parse_cli_arguments, denovo2DAE, export
from tools.tests.test_denovo2DAE import path
from DAE import pheno
from tools.tests.fixtures.pheno_data import DB, DBS, populate_instruments


FAMILIES_COLUMNS = ['--familyId=familyId', '--sex=gender',
                    '--momId=momId', '--dadId=dadId']


def converted_dae(vs, fs, addition=[], start_slice=0):
    args = [path('dnv2dae/' + vs), path('dnv2dae/' + fs)] \
            + FAMILIES_COLUMNS[start_slice:] + addition
    return denovo2DAE(parse_cli_arguments(args))


@pytest.fixture(scope='session')
def dae():
    return converted_dae('vs.tsv', 'fs.ped')


@pytest.fixture(scope='session')
def dae_force():
    return converted_dae('vs.tsv', 'fs.ped', ['--force'])


@pytest.fixture(scope='session')
def dae_ids():
    return converted_dae('vs.tsv', 'fs.ped', start_slice=1)


@pytest.fixture(scope='session')
def dae_file(dae, request):
    out = path('dnv2dae/out.tsv')
    export(out, dae)
    request.addfinalizer(lambda: os.remove(out))
    return out


@pytest.fixture(scope='session')
def dae_xlsx():
    return converted_dae('yuen_subset.xlsx', 'yuen_families.ped')


@pytest.fixture(scope='session')
def dae_csv():
    return converted_dae('yuen_subset.csv', 'yuen_families.ped')


@pytest.fixture(scope='session')
def dae_tsv():
    return converted_dae('yuen_subset.tsv', 'yuen_families.ped')


@pytest.fixture(scope='session')
def dae_with_columns():
    columns = ['-si=SAMPLE', '-c=CHROM', '-p=START', '-r=REF', '-a=ALT']
    return converted_dae('yuen_subset_cols.csv', 'yuen_families.ped', columns)


@pytest.fixture(scope='session')
def dae_zero_based(dae_tsv):
    d = converted_dae('yuen_subset.csv', 'yuen_families.ped', ['--zerobased'])
    return dae_tsv, d


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
