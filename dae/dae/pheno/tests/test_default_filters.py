'''
Created on Oct 18, 2016

@author: lubo
'''
import pytest


@pytest.mark.parametrize('filter_type,expected_len', [
    ('apply', 176),
    ('invert', 19),
    ('skip', 195)
])
def test_default_filters(fphdb, filter_type, expected_len):
    measure_id = 'i1.m10'
    assert measure_id in fphdb.measures and \
        fphdb.measures[measure_id] is not None
    df = fphdb.get_measure_values_df(measure_id, default_filter=filter_type)
    assert len(df) == expected_len


def test_default_filter_bad_value_throw(fphdb):
    measure_id = 'i1.m10'
    assert measure_id in fphdb.measures and \
        fphdb.measures[measure_id] is not None

    with pytest.raises(ValueError):
        fphdb.get_measure_values_df(measure_id, default_filter='wrong')
