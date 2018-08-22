import pytest
from denovo2DAE import parse_cli_arguments, denovo2DAE, output_filename, export
from tools.tests.test_denovo2DAE import path


@pytest.fixture(scope='session')
def dae():
    args = [path('dnv2dae/lelieveld-2016.tsv'),
            path('dnv2dae/lelieveld-2016-families.tsv')]
    return denovo2DAE(parse_cli_arguments(args))


@pytest.fixture(scope='session')
def dae_without_columns_error():
    args = [path('dnv2dae/lelieveld-2016-err.tsv'),
            path('dnv2dae/lelieveld-2016-families.tsv')]
    return parse_cli_arguments(args)


@pytest.fixture(scope='session')
def dae_file():
    out = path('dnv2dae/dae.tsv')
    path_args = [path('dnv2dae/yuen_subset.csv'),
                 path('dnv2dae/yuen_families.ped'), '-f', out]
    args = parse_cli_arguments(path_args)
    export(output_filename(args), denovo2DAE(args))
    return out


@pytest.fixture(scope='session')
def dae_with_columns():
    args = [path('dnv2dae/yuen_subset_cols.csv'),
            path('dnv2dae/yuen_families.ped'), '-i=SAMPLE',
            '-c=CHROM', '-p=START', '-r=REF', '-a=ALT']
    return denovo2DAE(parse_cli_arguments(args))


@pytest.fixture(scope='session')
def dae_xlsx():
    args = [path('dnv2dae/yuen_subset.xlsx'),
            path('dnv2dae/yuen_families.ped'), '--skiprows=1']
    return denovo2DAE(parse_cli_arguments(args))


@pytest.fixture(scope='session')
def dae_zero_based():
    args = [path('dnv2dae/yuen_subset.csv'), path('dnv2dae/yuen_families.ped')]
    return denovo2DAE(parse_cli_arguments(args)), \
        denovo2DAE(parse_cli_arguments(args + ['--zerobased']))
