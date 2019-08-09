'''
Created on Sep 12, 2016

@author: lubo
'''
import pytest
import pandas as pd
import numpy as np
from dae.pheno.common import MeasureType
from dae.pheno.pheno_db import Measure, PhenoDB


def df_check(df, expected_count, expected_cols):
    assert df is not None
    # FIXME Should we drop na vals, and when?
    # df = df.dropna()
    assert all([col in df for col in expected_cols])
    assert expected_count == len(df)


def dict_check(dict_, expected_count, expected_cols):
    assert isinstance(dict_, dict)
    for person, measures in dict_.items():
        assert all([col in measures for col in expected_cols])
    assert expected_count == len(dict_)


def dict_check_measure(dict_, expected_count, *args):
    assert isinstance(dict_, dict)
    for m_id, measure in dict_.items():
        assert isinstance(measure, Measure)
    assert expected_count == len(dict_)


def test_get_measure_type(fphdb):
    m = fphdb.get_measure('i1.m1')
    assert m.measure_type == MeasureType.continuous


@pytest.mark.parametrize('query_cols', [
    (['i1.m1']),
    (['i1.m1', 'i1.m2'])
])
@pytest.mark.parametrize('get,check', [
    (PhenoDB.get_values, dict_check),
    (PhenoDB.get_values_df, df_check)
])
def test_get_values(fphdb, query_cols, get, check):
    vals = get(fphdb, query_cols)
    check(vals, 195, query_cols)

    vals = get(fphdb, query_cols, ['f20.p1'])
    check(vals, 1, query_cols)

    vals = get(fphdb, query_cols, ['f20.p1', 'f21.p1'])
    check(vals, 2, query_cols)

    vals = get(fphdb, query_cols, roles=['prb'])
    check(vals, 39, query_cols)


@pytest.mark.parametrize('get,check', [
    (PhenoDB.get_instrument_values, dict_check),
    (PhenoDB.get_instrument_values_df, df_check)
])
def test_get_instrument_values(fphdb, get, check):
    values = get(fphdb, 'i1')
    check(values, 195, ['i1.m1', 'i1.m2', 'i1.m3', 'i1.m4',
                        'i1.m5', 'i1.m6', 'i1.m7', 'i1.m8',
                        'i1.m9', 'i1.m10'])


def test_has_measure(fphdb):
    measures = ['i1.m1', 'i1.m2', 'i1.m3', 'i1.m4',
                'i1.m5', 'i1.m6', 'i1.m7', 'i1.m8',
                'i1.m9', 'i1.m10']
    assert all([fphdb.has_measure(m) for m in measures])


@pytest.mark.parametrize('get,check', [
    (PhenoDB.get_measures, dict_check_measure),
    (PhenoDB._get_measures_df, df_check)
])
def test_get_measures(fphdb, get, check):
    expected_cols = ['measure_id', 'measure_name', 'instrument_name',
                     'description', 'individuals', 'measure_type',
                     'min_value', 'max_value', 'values_domain']

    measures = get(fphdb, measure_type='continuous')
    check(measures, 7, expected_cols)


def test_default_get_measure_df(fphdb):
    df = fphdb._get_measures_df()
    assert df is not None
    assert len(df) == 12


def test_get_persons_df(fphdb):
    prbs = fphdb.get_persons_df(roles=['prb'])
    assert len(prbs.columns) == 5
    df_check(prbs, 39, ['person_id', 'family_id', 'role',
                        'sex', 'status'])


def test_get_persons_values_df(fphdb):
    pvdf = fphdb.get_persons_values_df(['i1.m1'])
    assert len(pvdf) > 0


@pytest.mark.parametrize('families,expected_count', [
    (['f20'], 5),
    (['f20', 'f21'], 10)
])
@pytest.mark.parametrize('query_cols', [
    (['i1.m1']),
    (['i1.m1', 'i1.m2'])
])
def test_get_values_families_filter(fphdb, families,
                                    expected_count, query_cols):
    personlist = ['{}.dad', '{}.mom', '{}.p1']
    vals = fphdb.get_values(query_cols, family_ids=families)
    for f in families:
        assert all([p.format(f) in vals for p in personlist])
    dict_check(vals, expected_count, query_cols)


def test_min_max_measure_values(fphdb):
    measures = fphdb.get_measures()

    for measure in measures.values():
        if measure.measure_type == MeasureType.categorical or \
                measure.measure_type == MeasureType.raw:
            continue
        mmin = measure.min_value
        mmax = measure.max_value
        df = fphdb.get_measure_values_df(measure.measure_id,
                                         default_filter='skip')
        df = df[pd.to_numeric(
                    df[measure.measure_id], errors='coerce').notnull()]
        error = np.abs(mmin - df[measure.measure_id].min())
        assert error < 1E-5, measure.measure_id

        error = np.abs(mmax - df[measure.measure_id].max())
        assert error < 1E-5, measure.measure_id
