# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pytest

from dae.person_filters import (
    FamilyFilter,
    PhenoFilterRange,
    PhenoFilterSet,
    make_pheno_filter,
)
from dae.person_filters.person_filters import make_pheno_filter_beta
from dae.pheno.pheno_data import PhenotypeStudy


@pytest.fixture
def fake_phenotype_data(fixture_dirname):
    return PhenotypeStudy(
        "fake_db", fixture_dirname("fake_pheno_db/fake_i1.db"))


def test_pheno_filter_set_apply(fake_phenotype_data):
    df = fake_phenotype_data.get_people_measure_values_df(["i1.m5"])
    assert len(df) == 195

    measure = fake_phenotype_data.get_measure("i1.m5")

    pheno_filter = PhenoFilterSet(
        measure, {"catB", "catF"}, fake_phenotype_data)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 77
    assert set(filtered_df["i1.m5"]) == {"catB", "catF"}

    pheno_filter = PhenoFilterSet(measure, ["catF"], fake_phenotype_data)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 33
    assert set(filtered_df["i1.m5"]) == {"catF"}


def test_pheno_filter_set_noncategorical_measure(fake_phenotype_data):
    measure = fake_phenotype_data.get_measure("i1.m1")
    with pytest.raises(AssertionError):
        PhenoFilterSet(measure, ["a", "b", "c"], fake_phenotype_data)


def test_pheno_filter_set_values_set_type(fake_phenotype_data):
    measure = fake_phenotype_data.get_measure("i1.m5")
    with pytest.raises(TypeError):
        PhenoFilterSet(measure, "a", fake_phenotype_data)

    with pytest.raises(TypeError):
        PhenoFilterSet(measure, {"a": "b"}, fake_phenotype_data)


@pytest.mark.parametrize(
    "values_range", [((0.1234, 1.5678)), ([0.1234, 1.5678])],
)
def test_pheno_filter_min_max_assignment(fake_phenotype_data, values_range):
    measure = fake_phenotype_data.get_measure("i1.m1")
    pheno_filter = PhenoFilterRange(measure, values_range, fake_phenotype_data)
    assert hasattr(pheno_filter, "values_min")
    assert hasattr(pheno_filter, "values_max")
    assert pheno_filter.values_min == pytest.approx(0.1234, abs=1e-5)
    assert pheno_filter.values_max == pytest.approx(1.5678, abs=1e-5)


def test_pheno_filter_range_apply(fake_phenotype_data):
    df = fake_phenotype_data.get_people_measure_values_df(["i1.m1"])
    assert len(df) == 195

    measure = fake_phenotype_data.get_measure("i1.m1")

    pheno_filter = PhenoFilterRange(measure, (50, 70), fake_phenotype_data)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 44
    for value in list(filtered_df["i1.m1"]):
        assert value > 50.0
        assert value < 70.0

    pheno_filter = PhenoFilterRange(measure, [70, 80], fake_phenotype_data)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 30
    for value in list(filtered_df["i1.m1"]):
        assert value > 70.0
        assert value < 80.0

    pheno_filter = PhenoFilterRange(measure, (None, 70), fake_phenotype_data)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 53
    for value in list(filtered_df["i1.m1"]):
        assert value < 70.0

    pheno_filter = PhenoFilterRange(measure, (50, None), fake_phenotype_data)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 186
    for value in list(filtered_df["i1.m1"]):
        assert value > 50.0

    pheno_filter = PhenoFilterRange(measure, (None, None), fake_phenotype_data)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 195

    pheno_filter = PhenoFilterRange(measure, {50}, fake_phenotype_data)
    print(df.head())
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 0


def test_pheno_filter_range_measure_type(fake_phenotype_data):
    measure = fake_phenotype_data.get_measure("i1.m5")
    with pytest.raises(AssertionError):
        PhenoFilterRange(measure, (0, 0), fake_phenotype_data)

    measure = fake_phenotype_data.get_measure("i1.m6")
    with pytest.raises(AssertionError):
        PhenoFilterRange(measure, (0, 0), fake_phenotype_data)


def test_pheno_filter_range_values_range_type(fake_phenotype_data):
    measure = fake_phenotype_data.get_measure("i1.m1")
    with pytest.raises(TypeError):
        PhenoFilterRange(measure, 0, fake_phenotype_data)  # type: ignore

    with pytest.raises(TypeError):
        PhenoFilterRange(measure, {0: 1}, fake_phenotype_data)

    with pytest.raises(TypeError):
        PhenoFilterRange(measure, {0, 1}, fake_phenotype_data)


def test_make_pheno_filter_categorical(fake_phenotype_data):
    pheno_filter = make_pheno_filter({
        "source": "i1.m5",
        "sourceType": "categorical",
        "selection": {"selection": {"catB", "catF"}},
    }, fake_phenotype_data)
    assert isinstance(pheno_filter, PhenoFilterSet)


def test_make_pheno_filter_categorical_beta(fake_phenotype_data):
    pheno_filter = make_pheno_filter_beta({
        "source": "i1.m5",
        "histogramType": "categorical",
        "values": {"catB", "catF"},
        "isFamily": False,
    }, fake_phenotype_data)
    assert isinstance(pheno_filter, PhenoFilterSet)


def test_make_pheno_filter_raw(fake_phenotype_data):
    with pytest.raises(AssertionError):
        make_pheno_filter({
            "source": "i1.m9",
            "sourceType": "categorical",
            "selection": {"selection": [0, 0]},
        }, fake_phenotype_data)


def test_make_pheno_filter_raw_beta(fake_phenotype_data):
    with pytest.raises(AssertionError):
        make_pheno_filter_beta({
            "source": "i1.m9",
            "histogramType": "categorical",
            "values": [0, 0],
            "isFamily": False,
        }, fake_phenotype_data)


def test_make_pheno_filter_continuous(fake_phenotype_data):
    pheno_filter = make_pheno_filter({
        "source": "i1.m1",
        "sourceType": "continuous",
        "selection": {"min": 50, "max": 70},
    }, fake_phenotype_data)
    assert isinstance(pheno_filter, PhenoFilterRange)


def test_make_pheno_filter_continuous_beta(fake_phenotype_data):
    pheno_filter = make_pheno_filter_beta({
        "source": "i1.m1",
        "histogramType": "continuous",
        "isFamily": False,
        "min": 50,
        "max": 70,
    }, fake_phenotype_data)
    assert isinstance(pheno_filter, PhenoFilterRange)


def test_make_pheno_filter_ordinal(fake_phenotype_data):
    pheno_filter = make_pheno_filter({
        "source": "i1.m4",
        "sourceType": "continuous",
        "selection": {"min": 3, "max": 5},
    }, fake_phenotype_data)
    assert isinstance(pheno_filter, PhenoFilterRange)


def test_make_pheno_filter_ordinal_beta(fake_phenotype_data):
    pheno_filter = make_pheno_filter_beta({
        "source": "i1.m4",
        "histogramType": "continuous",
        "isFamily": False,
        "min": 3,
        "max": 5,
    }, fake_phenotype_data)
    assert isinstance(pheno_filter, PhenoFilterRange)


def test_make_pheno_filter_nonexistent_measure(fake_phenotype_data):
    with pytest.raises(AssertionError):
        make_pheno_filter({
            "source": "??.??",
            "sourceType": "continuous",
            "selection": {"min": 0, "max": 0},
        }, fake_phenotype_data)


def test_make_pheno_filter_nonexistent_measure_beta(fake_phenotype_data):
    with pytest.raises(AssertionError):
        make_pheno_filter_beta({
            "source": "??.??",
            "histogramType": "continuous",
            "isFamily": False,
            "min": 0,
            "max": 0,
        }, fake_phenotype_data)


def test_make_pheno_filter_family(fake_phenotype_data):
    pheno_filter = make_pheno_filter({
        "source": "i1.m4",
        "sourceType": "continuous",
        "selection": {"min": 3, "max": 5},
        "role": "prb",
    }, fake_phenotype_data)
    assert isinstance(pheno_filter, FamilyFilter)
    assert isinstance(pheno_filter.person_filter, PhenoFilterRange)


def test_make_pheno_filter_family_beta(fake_phenotype_data):
    pheno_filter = make_pheno_filter_beta({
        "source": "i1.m4",
        "histogramType": "continuous",
        "isFamily": True,
        "min": 3,
        "max": 5,
    }, fake_phenotype_data)
    assert isinstance(pheno_filter, FamilyFilter)
    assert isinstance(pheno_filter.person_filter, PhenoFilterRange)
