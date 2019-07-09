import pytest
from pheno_tool.pheno_common import PhenoFilter, \
    PhenoFilterSet, PhenoFilterRange, PhenoFilterBuilder


def test_pheno_filter_nonexistent_measure(fake_pheno_db):
    with pytest.raises(AssertionError):
        PhenoFilter(fake_pheno_db, '??.??')


def test_pheno_filter_set_apply(fake_pheno_db):
    df = fake_pheno_db.get_persons_values_df(['i1.m5'])
    assert len(df) == 195

    pf = PhenoFilterSet(fake_pheno_db, 'i1.m5', {'catB', 'catF'})
    filtered_df = pf.apply(df)
    assert len(filtered_df) == 77
    assert set(filtered_df['i1.m5']) == {'catB', 'catF'}

    pf = PhenoFilterSet(fake_pheno_db, 'i1.m5', ['catF'])
    filtered_df = pf.apply(df)
    assert len(filtered_df) == 33
    assert set(filtered_df['i1.m5']) == {'catF'}


def test_pheno_filter_set_noncategorical_measure(fake_pheno_db):
    with pytest.raises(AssertionError):
        PhenoFilterSet(fake_pheno_db, 'i1.m1', ['a', 'b', 'c'])


def test_pheno_filter_set_values_set_type(fake_pheno_db):
    with pytest.raises(AssertionError):
        PhenoFilterSet(fake_pheno_db, 'i1.m5', 'a')

    with pytest.raises(AssertionError):
        PhenoFilterSet(fake_pheno_db, 'i1.m5', {'a': 'b'})


@pytest.mark.parametrize('values_range', [
    ((0.1234, 1.5678)),
    ([0.1234, 1.5678])
])
def test_pheno_filter_min_max_assignment(fake_pheno_db, values_range):
    pf = PhenoFilterRange(fake_pheno_db, 'i1.m1', values_range)
    assert hasattr(pf, 'values_min')
    assert hasattr(pf, 'values_max')
    assert pf.values_min == pytest.approx(0.1234, abs=1e-5)
    assert pf.values_max == pytest.approx(1.5678, abs=1e-5)


def test_pheno_filter_range_apply(fake_pheno_db):
    df = fake_pheno_db.get_persons_values_df(['i1.m1'])
    assert len(df) == 195

    pf = PhenoFilterRange(fake_pheno_db, 'i1.m1', (50, 70))
    filtered_df = pf.apply(df)
    assert len(filtered_df) == 44
    for value in list(filtered_df['i1.m1']):
        assert value > 50.0 and value < 70.0

    pf = PhenoFilterRange(fake_pheno_db, 'i1.m1', [70, 80])
    filtered_df = pf.apply(df)
    assert len(filtered_df) == 30
    for value in list(filtered_df['i1.m1']):
        assert value > 70.0 and value < 80.0

    pf = PhenoFilterRange(fake_pheno_db, 'i1.m1', (None, 70))
    filtered_df = pf.apply(df)
    assert len(filtered_df) == 53
    for value in list(filtered_df['i1.m1']):
        assert value < 70.0

    pf = PhenoFilterRange(fake_pheno_db, 'i1.m1', (50, None))
    filtered_df = pf.apply(df)
    assert len(filtered_df) == 186
    for value in list(filtered_df['i1.m1']):
        assert value > 50.0

    pf = PhenoFilterRange(fake_pheno_db, 'i1.m1', (None, None))
    filtered_df = pf.apply(df)
    assert len(filtered_df) == 195


def test_pheno_filter_range_measure_type(fake_pheno_db):
    with pytest.raises(AssertionError):
        PhenoFilterRange(fake_pheno_db, 'i1.m5', (0, 0))

    with pytest.raises(AssertionError):
        PhenoFilterRange(fake_pheno_db, 'i1.m6', (0, 0))


def test_pheno_filter_range_values_range_type(fake_pheno_db):
    with pytest.raises(AssertionError):
        PhenoFilterRange(fake_pheno_db, 'i1.m1', 0)

    with pytest.raises(AssertionError):
        PhenoFilterRange(fake_pheno_db, 'i1.m1', {0: 1})

    with pytest.raises(AssertionError):
        PhenoFilterRange(fake_pheno_db, 'i1.m1', {0, 1})


def test_pheno_filter_builder_categorical(fake_pheno_db):
    pf_builder = PhenoFilterBuilder(fake_pheno_db)
    pf = pf_builder.make_filter('i1.m5', {'catB', 'catF'})
    assert isinstance(pf, PhenoFilterSet)


def test_pheno_filter_builder_raw(fake_pheno_db):
    with pytest.raises(AssertionError):
        pf_builder = PhenoFilterBuilder(fake_pheno_db)
        pf_builder.make_filter('i1.m9', [0, 0])


def test_pheno_filter_builder_continuous(fake_pheno_db):
    pf_builder = PhenoFilterBuilder(fake_pheno_db)
    pf = pf_builder.make_filter('i1.m1', (50, 70))
    assert isinstance(pf, PhenoFilterRange)


def test_pheno_filter_builder_ordinal(fake_pheno_db):
    pf_builder = PhenoFilterBuilder(fake_pheno_db)
    pf = pf_builder.make_filter('i1.m4', (3, 5))
    assert isinstance(pf, PhenoFilterRange)


def test_pheno_filter_builder_nonexistent_measure(fake_pheno_db):
    pfbuilder = PhenoFilterBuilder(fake_pheno_db)
    with pytest.raises(AssertionError):
        pfbuilder.make_filter('??.??', (0, 0))
