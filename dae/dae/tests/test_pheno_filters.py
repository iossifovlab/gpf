import pytest
from dae.pheno.pheno_db import PhenotypeStudy
from dae.person_filters import \
    FamilyFilter, \
    PhenoFilterSet, \
    PhenoFilterRange, \
    make_pheno_filter


@pytest.fixture
def fake_phenotype_data(fixture_dirname):
    pheno_data = PhenotypeStudy(
        "fake_db", fixture_dirname("fake_pheno_db/fake.db"))
    pheno_data._load()
    return pheno_data


def test_pheno_filter_set_apply(fake_phenotype_data):
    df = fake_phenotype_data.get_persons_values_df(["i1.m5"])
    assert len(df) == 195

    measure = fake_phenotype_data.get_measure("i1.m5")

    pf = PhenoFilterSet(measure, {"catB", "catF"}, fake_phenotype_data)
    filtered_df = pf.apply_to_df(df)
    assert len(filtered_df) == 77
    assert set(filtered_df["i1.m5"]) == {"catB", "catF"}

    pf = PhenoFilterSet(measure, ["catF"], fake_phenotype_data)
    filtered_df = pf.apply_to_df(df)
    assert len(filtered_df) == 33
    assert set(filtered_df["i1.m5"]) == {"catF"}


def test_pheno_filter_set_noncategorical_measure(fake_phenotype_data):
    with pytest.raises(AssertionError):
        measure = fake_phenotype_data.get_measure("i1.m1")
        PhenoFilterSet(measure, ["a", "b", "c"], fake_phenotype_data)


def test_pheno_filter_set_values_set_type(fake_phenotype_data):
    measure = fake_phenotype_data.get_measure("i1.m5")
    with pytest.raises(TypeError):
        PhenoFilterSet(measure, "a", fake_phenotype_data)

    with pytest.raises(TypeError):
        PhenoFilterSet(measure, {"a": "b"}, fake_phenotype_data)


@pytest.mark.parametrize(
    "values_range", [((0.1234, 1.5678)), ([0.1234, 1.5678])]
)
def test_pheno_filter_min_max_assignment(fake_phenotype_data, values_range):
    measure = fake_phenotype_data.get_measure("i1.m1")
    pf = PhenoFilterRange(measure, values_range, fake_phenotype_data)
    assert hasattr(pf, "values_min")
    assert hasattr(pf, "values_max")
    assert pf.values_min == pytest.approx(0.1234, abs=1e-5)
    assert pf.values_max == pytest.approx(1.5678, abs=1e-5)


def test_pheno_filter_range_apply(fake_phenotype_data):
    df = fake_phenotype_data.get_persons_values_df(["i1.m1"])
    assert len(df) == 195

    measure = fake_phenotype_data.get_measure("i1.m1")

    pf = PhenoFilterRange(measure, (50, 70), fake_phenotype_data)
    filtered_df = pf.apply_to_df(df)
    assert len(filtered_df) == 44
    for value in list(filtered_df["i1.m1"]):
        assert value > 50.0 and value < 70.0

    pf = PhenoFilterRange(measure, [70, 80], fake_phenotype_data)
    filtered_df = pf.apply_to_df(df)
    assert len(filtered_df) == 30
    for value in list(filtered_df["i1.m1"]):
        assert value > 70.0 and value < 80.0

    pf = PhenoFilterRange(measure, (None, 70), fake_phenotype_data)
    filtered_df = pf.apply_to_df(df)
    assert len(filtered_df) == 53
    for value in list(filtered_df["i1.m1"]):
        assert value < 70.0

    pf = PhenoFilterRange(measure, (50, None), fake_phenotype_data)
    filtered_df = pf.apply_to_df(df)
    assert len(filtered_df) == 186
    for value in list(filtered_df["i1.m1"]):
        assert value > 50.0

    pf = PhenoFilterRange(measure, (None, None), fake_phenotype_data)
    filtered_df = pf.apply_to_df(df)
    assert len(filtered_df) == 195

    pf = PhenoFilterRange(measure, {50}, fake_phenotype_data)
    print(df.head())
    filtered_df = pf.apply_to_df(df)
    assert len(filtered_df) == 0


def test_pheno_filter_range_measure_type(fake_phenotype_data):
    with pytest.raises(AssertionError):
        measure = fake_phenotype_data.get_measure("i1.m5")
        PhenoFilterRange(measure, (0, 0), fake_phenotype_data)

    with pytest.raises(AssertionError):
        measure = fake_phenotype_data.get_measure("i1.m6")
        PhenoFilterRange(measure, (0, 0), fake_phenotype_data)


def test_pheno_filter_range_values_range_type(fake_phenotype_data):
    measure = fake_phenotype_data.get_measure("i1.m1")
    with pytest.raises(TypeError):
        PhenoFilterRange(measure, 0, fake_phenotype_data)

    with pytest.raises(TypeError):
        PhenoFilterRange(measure, {0: 1}, fake_phenotype_data)

    with pytest.raises(TypeError):
        PhenoFilterRange(measure, {0, 1}, fake_phenotype_data)


def test_make_pheno_filter_categorical(fake_phenotype_data):
    pf = make_pheno_filter({
        "source": "i1.m5",
        "sourceType": "categorical",
        "selection": {"selection": {"catB", "catF"}}
    }, fake_phenotype_data)
    assert isinstance(pf, PhenoFilterSet)


def test_make_pheno_filter_raw(fake_phenotype_data):
    with pytest.raises(AssertionError):
        make_pheno_filter({
            "source": "i1.m9",
            "sourceType": "categorical",
            "selection": {"selection": [0, 0]}
        }, fake_phenotype_data)


def test_make_pheno_filter_continuous(fake_phenotype_data):
    pf = make_pheno_filter({
        "source": "i1.m1",
        "sourceType": "continuous",
        "selection": {"min": 50, "max": 70}
    }, fake_phenotype_data)
    assert isinstance(pf, PhenoFilterRange)


def test_make_pheno_filter_ordinal(fake_phenotype_data):
    pf = make_pheno_filter({
        "source": "i1.m4",
        "sourceType": "continuous",
        "selection": {"min": 3, "max": 5}
    }, fake_phenotype_data)
    assert isinstance(pf, PhenoFilterRange)


def test_make_pheno_filter_nonexistent_measure(fake_phenotype_data):
    with pytest.raises(AssertionError):
        make_pheno_filter({
            "source": "??.??",
            "sourceType": "continuous",
            "selection": {"min": 0, "max": 0}
        }, fake_phenotype_data)


def test_make_pheno_filter_family(fake_phenotype_data):
    pf = make_pheno_filter({
        "source": "i1.m4",
        "sourceType": "continuous",
        "selection": {"min": 3, "max": 5},
        "role": "prb"
    }, fake_phenotype_data)
    assert isinstance(pf, FamilyFilter)
    assert isinstance(pf.person_filter, PhenoFilterRange)
