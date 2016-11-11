'''
Created on Nov 9, 2016

@author: lubo
'''
import pytest
from pheno_tool.measures import NormalizedMeasure


def test_verbal_iq_count(measures):
    df = measures.get_measure_df('pheno_common.verbal_iq')
    assert 2757 == len(df)


def test_head_circumference(measures):
    df = measures.get_measure_df(
        'ssc_commonly_used.head_circumference')
    assert 2728 == len(df)


def test_ala_bala_measure_raises(measures):
    with pytest.raises(ValueError):
        measures.get_measure_df('ala_bala')


def test_verbal_iq_interval(measures):
    family_ids = measures.get_measure_families(
        'pheno_common.verbal_iq', 10, 20)
    assert 120 == len(family_ids)
    df = measures.get_measure_df(
        'pheno_common.verbal_iq')
    for family_id in family_ids:
        assert all(df[df['family_id'] ==
                      family_id]['pheno_common.verbal_iq'].values <= 20)
        assert all(df[df['family_id'] ==
                      family_id]['pheno_common.verbal_iq'].values >= 10)


def test_head_circumference_interval(measures):
    family_ids = measures.get_measure_families(
        'ssc_commonly_used.head_circumference', 49, 50)
    assert 102 == len(family_ids)
    df = measures.get_measure_df(
        'ssc_commonly_used.head_circumference')
    for family_id in family_ids:
        assert all(df[df['family_id'] == family_id][
            'ssc_commonly_used.head_circumference'].values <= 50)
        assert all(df[df['family_id'] == family_id][
            'ssc_commonly_used.head_circumference'].values >= 49)


@pytest.fixture(scope='module')
def head_circumference(request, measures):
    measure = NormalizedMeasure(
        'ssc_commonly_used.head_circumference', measures)
    return measure


def test_head_circumference_created(head_circumference):
    assert head_circumference is not None


def test_head_circumference_check_df(head_circumference):
    measure = head_circumference
    df = measure.df
    assert 'family_id' in df.columns
    assert 'pheno_common.age' in df.columns
    assert 'pheno_common.non_verbal_iq' in df.columns

    assert 'ssc_commonly_used.head_circumference' in df.columns


def test_head_circumference_normalize_by_age(head_circumference):
    measure = head_circumference
    fitted = measure.normalize(['pheno_common.age'])
    assert fitted is not None


def test_head_circumference_normalize_by_couple(head_circumference):
    measure = head_circumference
    fitted = measure.normalize(
        ['pheno_common.age', 'pheno_common.non_verbal_iq'])
    assert fitted is not None


def test_head_circumference_normalize_by_wrong_value(head_circumference):
    measure = head_circumference
    with pytest.raises(AssertionError):
        measure.normalize(['ala_bala_portokala'])


def test_head_circumference_normalize_by_mixed_wrong_value(head_circumference):
    measure = head_circumference
    with pytest.raises(AssertionError):
        measure.normalize(['age', 'ala_bala_portokala'])


@pytest.fixture(scope='module')
def verbal_iq(request, measures):
    measure = NormalizedMeasure(
        'pheno_common.verbal_iq', measures)
    return measure


def test_verbal_iq_created(verbal_iq):
    measure = verbal_iq
    assert measure is not None


def test_verbal_iq_check_df(verbal_iq):
    measure = verbal_iq
    df = measure.df
    assert 'family_id' in df.columns
    assert 'pheno_common.age' in df.columns
    assert 'pheno_common.non_verbal_iq' in df.columns
    assert 'pheno_common.verbal_iq' in df.columns


def test_verbal_iq_normalize_by_verbal_iq(verbal_iq):
    measure = verbal_iq
    measure.normalize(['pheno_common.non_verbal_iq'])
    df = measure.df
    assert 'family_id' in df.columns
    assert 'person_id' in df.columns
    assert 'pheno_common.age' in df.columns
    assert 'pheno_common.non_verbal_iq' in df.columns
    assert 'pheno_common.verbal_iq' in df.columns


def test_verbal_iq_interval_with_family_counters(measures, verbal_iq):
    proband_ids = measures.get_measure_probands(
        'pheno_common.verbal_iq', 10, 20)

    assert 120 == len(proband_ids)
    df = measures.get_measure_df('pheno_common.verbal_iq')
    for proband_id in proband_ids:
        assert all(df[df['person_id'] ==
                      proband_id]['pheno_common.verbal_iq'].values <= 20)
        assert all(df[df['person_id'] ==
                      proband_id]['pheno_common.verbal_iq'].values >= 10)
