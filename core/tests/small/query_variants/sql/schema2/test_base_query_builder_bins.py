# The tests call the private methods of BaseQueryBuilder (W0212), and
# pytest passes fixtures as arguments of the same name (W0621). The test
# names describe each test, so the tests carry no docstrings (C0114, C0116).
# pylint: disable=W0621,C0114,C0116,W0212
import pathlib
from typing import Any

import pandas as pd
import pytest

from gpf.pedigrees.families_data import FamiliesData
from gpf.query_variants.sql.schema2.base_query_builder import (
    BaseQueryBuilder,
    Dialect,
    RealAttrFilterType,
)
from gpf.query_variants.sql.schema2.family_builder import FamilyQueryBuilder
from gpf.query_variants.sql.schema2.summary_builder import SummaryQueryBuilder
from gpf.variants.attributes import Role, Sex, Status

from .test_query_builders import (
    FAMILY_VARIANT_SCHEMA,
    NO_PARTITIONING_PROPERTIES,
    PEDIGREE_SCHEMA,
    SUMMARY_ALLELE_SCHEMA,
    _builder,
)

ALL_BINS = {"0", "1", "2", "3"}
RARE_BINS = {"0", "1", "2"}
ULTRA_RARE_BINS = {"0", "1"}


@pytest.fixture(scope="module")
def families() -> FamiliesData:
    resources_dir = pathlib.Path(__file__).parent / "resources"
    ped_df = pd.read_csv(resources_dir / "pedigree_table.csv")
    ped_df["role"] = pd.Series(
        [Role.from_name(v) for v in ped_df["role"]], index=ped_df.index)
    ped_df["sex"] = pd.Series(
        [Sex.from_name(v) for v in ped_df["sex"]], index=ped_df.index)
    ped_df["status"] = pd.Series(
        [Status.from_name(v) for v in ped_df["status"]], index=ped_df.index)
    return FamiliesData.from_pedigree_df(ped_df)


@pytest.fixture
def builder(families: FamiliesData) -> SummaryQueryBuilder:
    return _builder(Dialect(), families)


@pytest.fixture
def family_query_builder(families: FamiliesData) -> FamilyQueryBuilder:
    return FamilyQueryBuilder(
        dialect=Dialect(),
        db="db",
        family_variant_table="family_alleles",
        summary_allele_table="summary_alleles",
        pedigree_table="pedigree",
        family_variant_schema=FAMILY_VARIANT_SCHEMA,
        summary_allele_schema=SUMMARY_ALLELE_SCHEMA,
        table_properties=NO_PARTITIONING_PROPERTIES,
        pedigree_schema=PEDIGREE_SCHEMA,
        families=families,
        gene_models=None,
    )


@pytest.fixture(params=["family", "summary"])
def any_builder(
    request: pytest.FixtureRequest,
    family_query_builder: FamilyQueryBuilder,
    builder: SummaryQueryBuilder,
) -> BaseQueryBuilder:
    if request.param == "family":
        return family_query_builder
    return builder


def _bins(
    builder: BaseQueryBuilder, *,
    inheritance: str | list[str] | None = None,
    ultra_rare: bool | None = None,
    frequency_filter: RealAttrFilterType | None = None,
    rare_boundary: float = 5.0,
) -> set[str]:
    return builder._build_frequency_bin_heuristic_compute_bins(
        inheritance=inheritance,
        ultra_rare=ultra_rare,
        frequency_filter=frequency_filter,
        rare_boundary=rare_boundary,
    )


# _build_frequency_bin_heuristic_compute_bins


def test_bins_no_inheritance_no_filters_is_empty(
    builder: SummaryQueryBuilder,
) -> None:
    assert _bins(builder) == set()


def test_bins_no_inheritance_ultra_rare(
    builder: SummaryQueryBuilder,
) -> None:
    assert _bins(builder, ultra_rare=True) == ULTRA_RARE_BINS


@pytest.mark.parametrize("inheritance", ["denovo", ["denovo"]])
def test_bins_denovo_inheritance_scans_only_bin_zero(
    builder: SummaryQueryBuilder,
    inheritance: str | list[str],
) -> None:
    assert _bins(builder, inheritance=inheritance) == {"0"}


def test_bins_denovo_inheritance_ultra_rare_scans_only_bin_zero(
    builder: SummaryQueryBuilder,
) -> None:
    assert _bins(builder, inheritance="denovo", ultra_rare=True) == {"0"}


def test_bins_denovo_inheritance_with_frequency_filter_ignores_filter(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, inheritance="denovo",
        frequency_filter=[("af_allele_freq", (None, 10.0))])

    assert result == {"0"}


@pytest.mark.parametrize(
    "inheritance", ["mendelian", "omission", "unknown"])
def test_bins_inheritance_that_refuses_zero_is_empty(
    builder: SummaryQueryBuilder,
    inheritance: str,
) -> None:
    # The Mendelian check gives each matcher the value 0, so the
    # inheritance `mendelian` alone does not enter the check.
    assert _bins(builder, inheritance=inheritance) == set()
    assert _bins(builder, inheritance=inheritance, ultra_rare=True) == set()


@pytest.mark.parametrize("inheritance", ["not denovo", ["not mendelian"]])
def test_bins_inheritance_that_accepts_zero_scans_all_bins(
    builder: SummaryQueryBuilder,
    inheritance: str | list[str],
) -> None:
    assert _bins(builder, inheritance=inheritance) == ALL_BINS


def test_bins_inheritance_that_accepts_zero_ultra_rare(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(builder, inheritance="not denovo", ultra_rare=True)

    assert result == ULTRA_RARE_BINS


def test_bins_ultra_rare_wins_over_frequency_filter(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, ultra_rare=True,
        frequency_filter=[("af_allele_freq", (None, 10.0))])

    assert result == ULTRA_RARE_BINS


def test_bins_frequency_filter_end_below_boundary_scans_rare_bins(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, frequency_filter=[("af_allele_freq", (None, 1.0))])

    assert result == RARE_BINS


def test_bins_frequency_filter_end_at_boundary_scans_all_bins(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, frequency_filter=[("af_allele_freq", (None, 5.0))])

    assert result == ALL_BINS


def test_bins_frequency_filter_begin_at_boundary_scans_all_bins(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, frequency_filter=[("af_allele_freq", (5.0, None))])

    assert result == ALL_BINS


def test_bins_frequency_filter_begin_below_boundary_adds_nothing(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, frequency_filter=[("af_allele_freq", (1.0, None))])

    assert result == set()


def test_bins_frequency_filter_without_bounds_adds_nothing(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, frequency_filter=[("af_allele_freq", (None, None))])

    assert result == set()


def test_bins_frequency_filter_end_zero_counts_as_no_end(
    builder: SummaryQueryBuilder,
) -> None:
    # `if end and ...` treats an end of 0.0 like None. With a boundary of
    # 0.0 the end then reaches the `end >= rare_boundary` check.
    frequency_filter: RealAttrFilterType = [("af_allele_freq", (None, 0.0))]

    assert _bins(builder, frequency_filter=frequency_filter) == set()
    assert _bins(
        builder, frequency_filter=frequency_filter,
        rare_boundary=0.0) == ALL_BINS


def test_bins_frequency_filter_begin_zero_counts_as_no_begin(
    builder: SummaryQueryBuilder,
) -> None:
    # `if begin and ...` treats a begin of 0.0 like None, so a begin of 0.0
    # at a boundary of 0.0 adds nothing.
    result = _bins(
        builder, frequency_filter=[("af_allele_freq", (0.0, None))],
        rare_boundary=0.0)

    assert result == set()


def test_bins_filter_of_other_attribute_is_not_a_frequency_filter(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, frequency_filter=[("af_parents_freq", (None, 1.0))])

    assert result == set()


def test_bins_filter_of_other_attribute_falls_back_to_inheritance(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, inheritance="not denovo",
        frequency_filter=[("af_parents_freq", (None, 1.0))])

    assert result == ALL_BINS


def test_bins_frequency_filter_wins_over_inheritance_fallback(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, inheritance="not denovo",
        frequency_filter=[("af_allele_freq", (1.0, None))])

    assert result == set()


def test_bins_frequency_filter_reads_only_af_allele_freq_entries(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, frequency_filter=[
            ("af_parents_freq", (10.0, None)),
            ("af_allele_freq", (None, 1.0)),
        ])

    assert result == RARE_BINS


def test_bins_frequency_filter_unites_bins_of_each_entry(
    builder: SummaryQueryBuilder,
) -> None:
    result = _bins(
        builder, frequency_filter=[
            ("af_allele_freq", (None, 1.0)),
            ("af_allele_freq", (10.0, None)),
        ])

    assert result == ALL_BINS


# _build_real_attr_where


def test_real_attr_where_unknown_attribute_is_false(
    any_builder: BaseQueryBuilder,
) -> None:
    result = any_builder._build_real_attr_where([("no_such", (1.0, 2.0))])

    assert result == "false"


def test_real_attr_where_no_bounds_is_not_null(
    any_builder: BaseQueryBuilder,
) -> None:
    result = any_builder._build_real_attr_where(
        [("af_allele_freq", (None, None))])

    assert result == "(sa.af_allele_freq is not null)"


def test_real_attr_where_no_bounds_frequency_gives_no_fragment(
    any_builder: BaseQueryBuilder,
) -> None:
    result = any_builder._build_real_attr_where(
        [("af_allele_freq", (None, None))], is_frequency=True)

    assert result == ""


def test_real_attr_where_right_bound_only(
    any_builder: BaseQueryBuilder,
) -> None:
    result = any_builder._build_real_attr_where(
        [("af_allele_freq", (None, 0.5))])

    assert result == "(sa.af_allele_freq <= 0.5)"


def test_real_attr_where_right_bound_only_frequency_accepts_null(
    any_builder: BaseQueryBuilder,
) -> None:
    result = any_builder._build_real_attr_where(
        [("af_allele_freq", (None, 0.5))], is_frequency=True)

    assert result == (
        "(sa.af_allele_freq <= 0.5 or sa.af_allele_freq is null)")


@pytest.mark.parametrize("is_frequency", [False, True])
def test_real_attr_where_left_bound_only(
    any_builder: BaseQueryBuilder,
    *,
    is_frequency: bool,
) -> None:
    result = any_builder._build_real_attr_where(
        [("af_allele_freq", (0.1, None))], is_frequency=is_frequency)

    assert result == "(sa.af_allele_freq >= 0.1)"


@pytest.mark.parametrize("is_frequency", [False, True])
def test_real_attr_where_both_bounds(
    any_builder: BaseQueryBuilder,
    *,
    is_frequency: bool,
) -> None:
    result = any_builder._build_real_attr_where(
        [("af_allele_freq", (0.1, 0.5))], is_frequency=is_frequency)

    assert result == (
        "(sa.af_allele_freq >= 0.1 AND sa.af_allele_freq <= 0.5)")


def test_real_attr_where_int_attribute(
    any_builder: BaseQueryBuilder,
) -> None:
    result = any_builder._build_real_attr_where(
        [("af_allele_count", (1, 3))])

    assert result == "(sa.af_allele_count >= 1 AND sa.af_allele_count <= 3)"


def test_real_attr_where_joins_fragments_with_and(
    any_builder: BaseQueryBuilder,
) -> None:
    result = any_builder._build_real_attr_where([
        ("no_such", (1.0, 2.0)),
        ("af_allele_freq", (0.1, None)),
    ])

    assert result == "false AND (sa.af_allele_freq >= 0.1)"


def test_real_attr_where_empty_filter_is_empty(
    any_builder: BaseQueryBuilder,
) -> None:
    assert any_builder._build_real_attr_where([]) == ""


@pytest.mark.parametrize("bound", [True, "1", [1]])
def test_real_attr_where_refuses_bound_that_is_not_a_number(
    any_builder: BaseQueryBuilder,
    bound: Any,
) -> None:
    with pytest.raises(ValueError, match="invalid range bound"):
        any_builder._build_real_attr_where(
            [("af_allele_freq", (bound, None))])
    with pytest.raises(ValueError, match="invalid range bound"):
        any_builder._build_real_attr_where(
            [("af_allele_freq", (None, bound))])
