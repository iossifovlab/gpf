import pytest
import os
from denovo2DAE import *
from test_denovo2DAE import path


@pytest.fixture(scope='session')
def dae():
    return denovo2DAE(parse_cli_arguments([path('dnv2dae/lelieveld-2016.tsv'), \
            path('dnv2dae/lelieveld-2016-families.tsv')]))

@pytest.fixture(scope='session')
def dae_without_columns_error():
    return parse_cli_arguments([path('dnv2dae/lelieveld-2016-err.tsv'), \
            path('dnv2dae/lelieveld-2016-families.tsv')])

@pytest.fixture(scope='session')
def dae_file():
    out = path('dnv2dae/dae.tsv')
    args = parse_cli_arguments([path('dnv2dae/yuen_subset.csv'), \
            path('dnv2dae/yuen_families.ped'), '-f', out])
    export(output_filename(args), denovo2DAE(args))
    return out

@pytest.fixture(scope='session')
def dae_with_columns():
    return denovo2DAE(parse_cli_arguments([path('dnv2dae/yuen_subset_cols.csv'), \
            path('dnv2dae/yuen_families.ped'), '-i=SAMPLE', \
            '-c=CHROM', '-p=START', '-r=REF', '-a=ALT']))

@pytest.fixture(scope='session')
def dae_xlsx():
    return denovo2DAE(parse_cli_arguments([path('dnv2dae/yuen_subset.xlsx'), \
            path('dnv2dae/yuen_families.ped'), '--skiprows=1']))

@pytest.fixture(scope='session')
def dae_zero_based():
    return denovo2DAE(parse_cli_arguments([path('dnv2dae/yuen_subset.csv'), \
            path('dnv2dae/yuen_families.ped')])), \
        denovo2DAE(parse_cli_arguments([path('dnv2dae/yuen_subset.csv'), \
            path('dnv2dae/yuen_families.ped'), '--zerobased']))
