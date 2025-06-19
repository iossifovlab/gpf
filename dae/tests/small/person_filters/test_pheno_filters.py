# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
import pytest
from dae.person_filters import (
    FamilyFilter,
    PhenoFilterRange,
    PhenoFilterSet,
    make_pheno_filter,
)
from dae.person_filters.person_filters import make_pheno_filter_beta


def test_pheno_filter_set_apply(t4c8_study_1_pheno):
    df = t4c8_study_1_pheno.get_people_measure_values_df(["i1.m5"])
    assert len(df) == 16

    measure = t4c8_study_1_pheno.get_measure("i1.m5")

    pheno_filter = PhenoFilterSet(
        measure, {"val1", "val3"}, t4c8_study_1_pheno)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 10
    assert set(filtered_df["i1.m5"]) == {"val1", "val3"}

    pheno_filter = PhenoFilterSet(measure, ["val1"], t4c8_study_1_pheno)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 3
    assert set(filtered_df["i1.m5"]) == {"val1"}


def test_pheno_filter_set_noncategorical_measure(t4c8_study_1_pheno):
    measure = t4c8_study_1_pheno.get_measure("i1.m1")
    with pytest.raises(AssertionError):
        PhenoFilterSet(measure, ["a", "b", "c"], t4c8_study_1_pheno)


def test_pheno_filter_set_values_set_type(t4c8_study_1_pheno):
    measure = t4c8_study_1_pheno.get_measure("i1.m5")
    with pytest.raises(TypeError):
        PhenoFilterSet(measure, "a", t4c8_study_1_pheno)

    with pytest.raises(TypeError):
        PhenoFilterSet(measure, {"a": "b"}, t4c8_study_1_pheno)


@pytest.mark.parametrize(
    "values_range", [((0.1234, 1.5678)), ([0.1234, 1.5678])],
)
def test_pheno_filter_min_max_assignment(t4c8_study_1_pheno, values_range):
    measure = t4c8_study_1_pheno.get_measure("i1.m1")
    pheno_filter = PhenoFilterRange(measure, values_range, t4c8_study_1_pheno)
    assert hasattr(pheno_filter, "values_min")
    assert hasattr(pheno_filter, "values_max")
    assert pheno_filter.values_min == pytest.approx(0.1234, abs=1e-5)
    assert pheno_filter.values_max == pytest.approx(1.5678, abs=1e-5)


def test_pheno_filter_range_apply(t4c8_study_1_pheno):
    df = t4c8_study_1_pheno.get_people_measure_values_df(["i1.m1"])
    assert len(df) == 16

    measure = t4c8_study_1_pheno.get_measure("i1.m1")

    pheno_filter = PhenoFilterRange(measure, (50, 70), t4c8_study_1_pheno)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 4
    for value in list(filtered_df["i1.m1"]):
        assert value > 50.0
        assert value < 70.0

    pheno_filter = PhenoFilterRange(measure, [70, 80], t4c8_study_1_pheno)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 3
    for value in list(filtered_df["i1.m1"]):
        assert value > 70.0
        assert value < 80.0

    pheno_filter = PhenoFilterRange(measure, (None, 70), t4c8_study_1_pheno)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 5
    for value in list(filtered_df["i1.m1"]):
        assert value < 70.0

    pheno_filter = PhenoFilterRange(measure, (50, None), t4c8_study_1_pheno)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 15
    for value in list(filtered_df["i1.m1"]):
        assert value > 50.0

    pheno_filter = PhenoFilterRange(measure, (None, None), t4c8_study_1_pheno)
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 16

    pheno_filter = PhenoFilterRange(measure, {50}, t4c8_study_1_pheno)
    print(df.head())
    filtered_df = pheno_filter.apply_to_df(df)
    assert len(filtered_df) == 0


def test_pheno_filter_range_measure_type(t4c8_study_1_pheno):
    measure = t4c8_study_1_pheno.get_measure("i1.m5")
    with pytest.raises(AssertionError):
        PhenoFilterRange(measure, (0, 0), t4c8_study_1_pheno)


def test_pheno_filter_range_values_range_type(t4c8_study_1_pheno):
    measure = t4c8_study_1_pheno.get_measure("i1.m1")
    with pytest.raises(TypeError):
        PhenoFilterRange(measure, 0, t4c8_study_1_pheno)  # type: ignore

    with pytest.raises(TypeError):
        PhenoFilterRange(measure, {0: 1}, t4c8_study_1_pheno)

    with pytest.raises(TypeError):
        PhenoFilterRange(measure, {0, 1}, t4c8_study_1_pheno)


def test_make_pheno_filter_categorical(t4c8_study_1_pheno):
    pheno_filter = make_pheno_filter({
        "source": "i1.m5",
        "sourceType": "categorical",
        "selection": {"selection": {"catB", "catF"}},
    }, t4c8_study_1_pheno)
    assert isinstance(pheno_filter, PhenoFilterSet)


def test_make_pheno_filter_categorical_beta(t4c8_study_1_pheno):
    pheno_filter = make_pheno_filter_beta({
        "source": "i1.m5",
        "histogramType": "categorical",
        "values": {"catB", "catF"},
        "isFamily": False,
    }, t4c8_study_1_pheno)
    assert isinstance(pheno_filter, PhenoFilterSet)


def test_make_pheno_filter_raw(t4c8_study_1_pheno):
    with pytest.raises(AssertionError):
        make_pheno_filter({
            "source": "i1.m9",
            "sourceType": "categorical",
            "selection": {"selection": [0, 0]},
        }, t4c8_study_1_pheno)


def test_make_pheno_filter_raw_beta(t4c8_study_1_pheno):
    with pytest.raises(AssertionError):
        make_pheno_filter_beta({
            "source": "i1.m9",
            "histogramType": "categorical",
            "values": [0, 0],
            "isFamily": False,
        }, t4c8_study_1_pheno)


def test_make_pheno_filter_continuous(t4c8_study_1_pheno):
    pheno_filter = make_pheno_filter({
        "source": "i1.m1",
        "sourceType": "continuous",
        "selection": {"min": 50, "max": 70},
    }, t4c8_study_1_pheno)
    assert isinstance(pheno_filter, PhenoFilterRange)


def test_make_pheno_filter_continuous_beta(t4c8_study_1_pheno):
    pheno_filter = make_pheno_filter_beta({
        "source": "i1.m1",
        "histogramType": "continuous",
        "isFamily": False,
        "min": 50,
        "max": 70,
    }, t4c8_study_1_pheno)
    assert isinstance(pheno_filter, PhenoFilterRange)


def test_make_pheno_filter_ordinal(t4c8_study_1_pheno):
    pheno_filter = make_pheno_filter({
        "source": "i1.m4",
        "sourceType": "continuous",
        "selection": {"min": 3, "max": 5},
    }, t4c8_study_1_pheno)
    assert isinstance(pheno_filter, PhenoFilterRange)


def test_make_pheno_filter_ordinal_beta(t4c8_study_1_pheno):
    pheno_filter = make_pheno_filter_beta({
        "source": "i1.m4",
        "histogramType": "continuous",
        "isFamily": False,
        "min": 3,
        "max": 5,
    }, t4c8_study_1_pheno)
    assert isinstance(pheno_filter, PhenoFilterRange)


def test_make_pheno_filter_nonexistent_measure(t4c8_study_1_pheno):
    with pytest.raises(AssertionError):
        make_pheno_filter({
            "source": "??.??",
            "sourceType": "continuous",
            "selection": {"min": 0, "max": 0},
        }, t4c8_study_1_pheno)


def test_make_pheno_filter_nonexistent_measure_beta(t4c8_study_1_pheno):
    with pytest.raises(AssertionError):
        make_pheno_filter_beta({
            "source": "??.??",
            "histogramType": "continuous",
            "isFamily": False,
            "min": 0,
            "max": 0,
        }, t4c8_study_1_pheno)


def test_make_pheno_filter_family(t4c8_study_1_pheno):
    pheno_filter = make_pheno_filter({
        "source": "i1.m4",
        "sourceType": "continuous",
        "selection": {"min": 3, "max": 5},
        "role": "prb",
    }, t4c8_study_1_pheno)
    assert isinstance(pheno_filter, FamilyFilter)
    assert isinstance(pheno_filter.person_filter, PhenoFilterRange)


def test_make_pheno_filter_family_beta(t4c8_study_1_pheno):
    pheno_filter = make_pheno_filter_beta({
        "source": "i1.m4",
        "histogramType": "continuous",
        "isFamily": True,
        "min": 3,
        "max": 5,
    }, t4c8_study_1_pheno)
    assert isinstance(pheno_filter, FamilyFilter)
    assert isinstance(pheno_filter.person_filter, PhenoFilterRange)
