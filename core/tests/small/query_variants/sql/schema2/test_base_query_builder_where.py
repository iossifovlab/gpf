# The tests call the private methods of BaseQueryBuilder (W0212), and
# pytest passes fixtures as arguments of the same name (W0621). The test
# names describe each test, so the tests carry no docstrings (C0114, C0116).
# pylint: disable=W0621,C0114,C0116,W0212
from collections.abc import Callable
from typing import Any

import pytest
from gain.utils.regions import Region

from gpf.pedigrees.families_data import FamiliesData
from gpf.pedigrees.family import Person
from gpf.query_variants.sql.schema2.base_query_builder import (
    BaseQueryBuilder,
    Dialect,
)
from gpf.query_variants.sql.schema2.family_builder import FamilyQueryBuilder
from gpf.query_variants.sql.schema2.summary_builder import SummaryQueryBuilder

from .test_query_builders import (
    FAMILY_VARIANT_SCHEMA,
    NO_PARTITIONING_PROPERTIES,
    PEDIGREE_SCHEMA,
    SUMMARY_ALLELE_SCHEMA,
    _builder,
)

SEPARATOR = " AND \n    "


def _person(family_id: str, person_id: str, **attrs: Any) -> Person:
    return Person(
        family_id=family_id, person_id=person_id,
        sex="M", status="unaffected", role="dad", **attrs)


@pytest.fixture(scope="module")
def families() -> FamiliesData:
    return FamiliesData.from_family_persons({
        "f1": [
            _person("f1", "f1.dad", family_bin="3"),
            _person("f1", "f1.mom", family_bin="3"),
        ],
        "f2": [_person("f2", "f2.dad", family_bin="5")],
        "f3": [_person("f3", "f3.dad")],
    })


def _family_builder(
    families: FamiliesData, *,
    family_bin_in_variants: bool = False,
    family_bin_in_pedigree: bool = False,
    family_bin_size: int = 0,
    extra_variant_columns: tuple[str, ...] = (),
    extra_properties: dict[str, Any] | None = None,
) -> FamilyQueryBuilder:
    variant_schema = dict(FAMILY_VARIANT_SCHEMA)
    if family_bin_in_variants:
        variant_schema["family_bin"] = "int"
    for extra_column in extra_variant_columns:
        variant_schema[extra_column] = "int"
    pedigree_schema = dict(PEDIGREE_SCHEMA)
    if family_bin_in_pedigree:
        pedigree_schema["family_bin"] = "int"
    return FamilyQueryBuilder(
        dialect=Dialect(),
        db="db",
        family_variant_table="family_alleles",
        summary_allele_table="summary_alleles",
        pedigree_table="pedigree",
        family_variant_schema=variant_schema,
        summary_allele_schema=SUMMARY_ALLELE_SCHEMA,
        table_properties={
            **NO_PARTITIONING_PROPERTIES,
            "family_bin_size": family_bin_size,
            **(extra_properties or {}),
        },
        pedigree_schema=pedigree_schema,
        families=families,
        gene_models=None,
    )


@pytest.fixture
def family_builder(families: FamiliesData) -> FamilyQueryBuilder:
    return _family_builder(families)


@pytest.fixture
def binned_builder(families: FamiliesData) -> FamilyQueryBuilder:
    return _family_builder(
        families, family_bin_in_variants=True, family_bin_in_pedigree=True,
        family_bin_size=10)


@pytest.fixture
def summary_builder(families: FamiliesData) -> SummaryQueryBuilder:
    return _builder(Dialect(), families)


def _where(*fragments: str) -> str:
    joined = SEPARATOR.join(f"( {f} )" for f in fragments)
    return f"\n  WHERE\n    {joined}\n    "


def _bins_of(fragment: str, column: str = "fa.family_bin") -> set[str]:
    prefix = f"{column} IN ("
    assert fragment.startswith(prefix)
    assert fragment.endswith(")")
    return set(fragment[len(prefix):-1].split(","))


# _build_partition_bin_heuristic_where


def test_partition_bin_where_gives_empty_string_for_no_bins(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_partition_bin_heuristic_where(
        "family_id", [])

    assert result == ""


def test_partition_bin_where_gives_empty_string_when_all_bins_are_asked(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_partition_bin_heuristic_where(
        "family_id", ["1", "2"], 2)

    assert result == ""


def test_partition_bin_where_builds_in_clause_when_not_all_bins_are_asked(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_partition_bin_heuristic_where(
        "family_id", ["1", "2"], 3)

    assert result == "fa.family_id IN (1,2)"


def test_partition_bin_where_uses_fa_for_a_family_column(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_partition_bin_heuristic_where(
        "is_denovo", ["1"])

    assert result == "fa.is_denovo IN (1)"


def test_partition_bin_where_uses_sa_for_a_summary_column(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_partition_bin_heuristic_where(
        "chromosome", ["1"])

    assert result == "sa.chromosome IN (1)"


def test_partition_bin_where_joins_both_columns_with_and(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_partition_bin_heuristic_where(
        "allele_index", ["1"])

    assert result == "fa.allele_index IN (1) AND sa.allele_index IN (1)"


def test_partition_bin_where_gives_empty_string_for_unknown_column(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_partition_bin_heuristic_where(
        "no_such_column", ["1", "2"])

    assert result == ""


def test_partition_bin_where_joins_bins_in_iteration_order_without_space(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_partition_bin_heuristic_where(
        "chromosome", ["3", "1", "2"])

    assert result == "sa.chromosome IN (3,1,2)"


def test_partition_bin_where_quotes_str_bins(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_partition_bin_heuristic_where(
        "chromosome", ["chr1", "chr2"], str_bins=True)

    assert result == "sa.chromosome IN ('chr1','chr2')"


def test_partition_bin_where_does_not_escape_a_quote_in_str_bins(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_partition_bin_heuristic_where(
        "chromosome", ["a'b"], str_bins=True)

    assert result == "sa.chromosome IN ('a'b')"


# _build_family_bin_heuristic


def test_family_bin_heuristic_needs_family_bin_in_variant_schema(
    families: FamiliesData,
) -> None:
    builder = _family_builder(
        families, family_bin_in_pedigree=True, family_bin_size=10)

    result = builder._build_family_bin_heuristic(["f1"], ["f2.dad"])

    assert result == ""


def test_family_bin_heuristic_needs_family_bin_in_pedigree_schema(
    families: FamiliesData,
) -> None:
    builder = _family_builder(
        families, family_bin_in_variants=True, family_bin_size=10)

    result = builder._build_family_bin_heuristic(["f1"], ["f2.dad"])

    assert result == ""


def test_family_bin_heuristic_gives_bins_of_the_family_ids(
    binned_builder: FamilyQueryBuilder,
) -> None:
    result = binned_builder._build_family_bin_heuristic(["f1"], None)

    assert result == "fa.family_bin IN (3)"


def test_family_bin_heuristic_gives_bins_of_the_person_ids(
    binned_builder: FamilyQueryBuilder,
) -> None:
    result = binned_builder._build_family_bin_heuristic(None, ["f2.dad"])

    assert result == "fa.family_bin IN (5)"


def test_family_bin_heuristic_joins_bins_of_families_and_persons(
    binned_builder: FamilyQueryBuilder,
) -> None:
    result = binned_builder._build_family_bin_heuristic(["f1"], ["f2.dad"])

    assert _bins_of(result) == {"3", "5"}


def test_family_bin_heuristic_treats_empty_lists_like_none(
    binned_builder: FamilyQueryBuilder,
) -> None:
    result = binned_builder._build_family_bin_heuristic([], [])

    assert result == ""


def test_family_bin_heuristic_gives_none_for_a_person_without_a_bin(
    binned_builder: FamilyQueryBuilder,
) -> None:
    result = binned_builder._build_family_bin_heuristic(["f3"], None)

    assert result == "fa.family_bin IN (None)"


def test_family_bin_heuristic_gives_empty_string_when_all_bins_are_asked(
    families: FamiliesData,
) -> None:
    builder = _family_builder(
        families, family_bin_in_variants=True, family_bin_in_pedigree=True,
        family_bin_size=2)

    result = builder._build_family_bin_heuristic(["f1", "f2"], None)

    assert result == ""


# _build_where_string


def test_where_string_without_filters_keeps_only_alt_alleles(
    family_builder: FamilyQueryBuilder,
) -> None:
    assert family_builder._build_where_string() == _where(
        "sa.allele_index > 0")


def test_where_string_of_summary_builder_keeps_only_alt_alleles(
    summary_builder: SummaryQueryBuilder,
) -> None:
    assert summary_builder._build_where_string() == _where(
        "sa.allele_index > 0")


def test_where_string_is_empty_when_no_fragment_is_left(
    family_builder: FamilyQueryBuilder,
) -> None:
    assert family_builder._build_where_string(return_reference=True) == ""


def test_where_string_ignores_return_unknown_and_extra_kwargs(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        return_unknown=True, no_such_argument="x")

    assert result == _where("sa.allele_index > 0")


def _patch_gene_heuristic(
    monkeypatch: pytest.MonkeyPatch,
    builder: BaseQueryBuilder,
    result: list[Region],
) -> list[tuple[list[str], list[Region] | None]]:
    calls: list[tuple[list[str], list[Region] | None]] = []

    def fake(
        genes: list[str], regions: list[Region] | None,
    ) -> list[Region]:
        calls.append((genes, regions))
        return result

    monkeypatch.setattr(builder, "_build_gene_regions_heuristic", fake)
    return calls


GENE_REGION = Region("1", 10, 20)
GENE_REGION_WHERE = (
    "( sa.`chromosome` = '1' AND "
    "((sa.`position` >= 10 AND sa.`position` <= 20) OR "
    "(COALESCE(sa.`end_position`, -1) >= 10 AND "
    "COALESCE(sa.`end_position`, -1) <= 20) OR "
    "(10 >= sa.`position` AND 20 <= COALESCE(sa.`end_position`, -1))))"
)


def test_where_string_with_genes_and_effect_types_has_outer_parentheses(
    monkeypatch: pytest.MonkeyPatch,
    family_builder: FamilyQueryBuilder,
) -> None:
    _patch_gene_heuristic(monkeypatch, family_builder, [GENE_REGION])

    result = family_builder._build_where_string(
        genes=["G1"], effect_types=["missense"], return_reference=True)

    assert result == _where(
        "((  eg.effect_gene_symbols in (  'G1'  )  ) AND "
        "(  eg.effect_types in (  'missense'  )  ))",
        GENE_REGION_WHERE,
    )


def test_where_string_with_genes_only_has_no_outer_parentheses(
    monkeypatch: pytest.MonkeyPatch,
    family_builder: FamilyQueryBuilder,
) -> None:
    _patch_gene_heuristic(monkeypatch, family_builder, [GENE_REGION])

    result = family_builder._build_where_string(
        genes=["G1"], return_reference=True)

    assert result == _where(
        "(  eg.effect_gene_symbols in (  'G1'  )  )",
        GENE_REGION_WHERE,
    )


def test_where_string_passes_genes_and_regions_to_gene_heuristic(
    monkeypatch: pytest.MonkeyPatch,
    family_builder: FamilyQueryBuilder,
) -> None:
    calls = _patch_gene_heuristic(monkeypatch, family_builder, [GENE_REGION])
    regions = [Region("2", 1, 2)]

    family_builder._build_where_string(genes=["G1"], regions=regions)

    assert calls == [(["G1"], regions)]


def test_where_string_uses_gene_heuristic_result_instead_of_regions(
    monkeypatch: pytest.MonkeyPatch,
    family_builder: FamilyQueryBuilder,
) -> None:
    _patch_gene_heuristic(monkeypatch, family_builder, [GENE_REGION])
    region_bin_calls: list[list[Region] | None] = []

    def fake_region_bin(regions: list[Region] | None) -> str:
        region_bin_calls.append(regions)
        return ""

    monkeypatch.setattr(
        family_builder, "_build_region_bin_heuristic", fake_region_bin)

    result = family_builder._build_where_string(
        genes=["G1"], regions=[Region("2", 1, 2)], return_reference=True)

    assert GENE_REGION_WHERE in result
    assert "'2'" not in result
    assert region_bin_calls == [[GENE_REGION]]


def test_where_string_with_effect_types_only(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        effect_types=["missense"], return_reference=True)

    assert result == _where("(  eg.effect_types in (  'missense'  )  )")


def test_where_string_with_regions(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        regions=[GENE_REGION], return_reference=True)

    assert result == _where(GENE_REGION_WHERE)


def test_where_string_with_family_ids(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        family_ids=["f1"], return_reference=True)

    assert result == _where("(  fa.family_id in (  'f1'  )  )")


def test_where_string_with_empty_family_ids_gives_is_null(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        family_ids=[], return_reference=True)

    assert result == _where(" fa.family_id IS NULL")


def test_where_string_with_empty_family_ids_skips_family_bin_heuristic(
    binned_builder: FamilyQueryBuilder,
) -> None:
    result = binned_builder._build_where_string(
        family_ids=[], return_reference=True)

    assert result == _where(" fa.family_id IS NULL")


def test_where_string_with_family_ids_adds_family_bin_heuristic(
    binned_builder: FamilyQueryBuilder,
) -> None:
    result = binned_builder._build_where_string(
        family_ids=["f1"], return_reference=True)

    assert result == _where(
        "(  fa.family_id in (  'f1'  )  )",
        "fa.family_bin IN (3)",
    )


def test_where_string_with_person_ids_drops_duplicates(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        person_ids=["f1.dad", "f1.dad"], return_reference=True)

    assert result == _where("(  pi.item in (  'f1.dad'  )  )")


def test_where_string_passes_person_ids_to_family_bin_heuristic_as_set(
    monkeypatch: pytest.MonkeyPatch,
    family_builder: FamilyQueryBuilder,
) -> None:
    calls: list[tuple[Any, Any]] = []

    def fake(family_ids: Any, person_ids: Any) -> str:
        calls.append((family_ids, person_ids))
        return ""

    monkeypatch.setattr(family_builder, "_build_family_bin_heuristic", fake)

    family_builder._build_where_string(person_ids=["f1.dad"])

    assert calls == [(None, {"f1.dad"})]
    assert isinstance(calls[0][1], set)


def test_where_string_adds_one_fragment_per_inheritance_query(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        inheritance=["denovo", "mendelian"], return_reference=True)

    assert result == _where(
        "BITAND(inheritance_in_members, 4) <> 0",
        "BITAND(inheritance_in_members, 2) <> 0",
    )


@pytest.mark.parametrize(("argument", "value", "expected"), [
    ("roles", "prb", "BITAND(allele_in_roles, 128) <> 0"),
    ("sexes", "male", "BITAND(allele_in_sexes, 1) <> 0"),
    ("affected_statuses", "affected", "BITAND(allele_in_statuses, 2) <> 0"),
    ("variant_type", "sub", "BITAND(variant_type, 1) <> 0"),
])
def test_where_string_with_attribute_query(
    family_builder: FamilyQueryBuilder,
    argument: str, value: str, expected: str,
) -> None:
    kwargs: dict[str, Any] = {argument: value}

    result = family_builder._build_where_string(
        **kwargs, return_reference=True)

    assert result == _where(expected)


def test_where_string_with_real_attr_filter(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        real_attr_filter=[("af_allele_freq", (None, 1.0))],
        return_reference=True)

    assert result == _where("(sa.af_allele_freq <= 1.0)")


def test_where_string_with_categorical_attr_filter(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        categorical_attr_filter=[("family_id", ["x"])],
        return_reference=True)

    assert result == _where("fa.family_id = 'x'")


def test_where_string_with_frequency_filter(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        frequency_filter=[("af_allele_freq", (0.5, None))],
        return_reference=True)

    assert result == _where("(sa.af_allele_freq >= 0.5)")


@pytest.mark.parametrize("argument", ["real_attr_filter", "frequency_filter"])
def test_where_string_drops_an_empty_filter(
    family_builder: FamilyQueryBuilder, argument: str,
) -> None:
    kwargs: dict[str, Any] = {argument: []}

    result = family_builder._build_where_string(
        **kwargs, return_reference=True)

    assert result == ""


def test_where_string_with_ultra_rare(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        ultra_rare=True, return_reference=True)

    assert result == _where(
        "(sa.af_allele_count <= 1 or sa.af_allele_count is null)")


def test_where_string_ignores_false_ultra_rare(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        ultra_rare=False, return_reference=True)

    assert result == ""


def _returning(fragment: str) -> Callable[..., str]:
    def fake(*_args: Any, **_kwargs: Any) -> str:
        return fragment
    return fake


def test_where_string_appends_heuristics_last_and_in_order(
    monkeypatch: pytest.MonkeyPatch,
    family_builder: FamilyQueryBuilder,
) -> None:
    for name, fragment in [
        ("_build_return_reference_and_return_unknown", "RR"),
        ("_build_frequency_bin_heuristic", "FREQ"),
        ("_build_family_bin_heuristic", "FAM"),
        ("_build_coding_heuristic", "CODING"),
        ("_build_region_bin_heuristic", "REGION"),
    ]:
        monkeypatch.setattr(family_builder, name, _returning(fragment))

    result = family_builder._build_where_string(variant_type="sub")

    assert result == _where(
        "BITAND(variant_type, 1) <> 0",
        "RR", "FREQ", "FAM", "CODING", "REGION",
    )


def test_where_string_keeps_the_order_of_the_middle_fragments(
    family_builder: FamilyQueryBuilder,
) -> None:
    result = family_builder._build_where_string(
        family_ids=["f1"],
        person_ids=["f1.dad"],
        inheritance="denovo",
        roles="prb",
        sexes="male",
        affected_statuses="affected",
        variant_type="sub",
        real_attr_filter=[("af_allele_freq", (None, 1.0))],
        categorical_attr_filter=[("family_id", ["x"])],
        frequency_filter=[("af_allele_freq", (0.5, None))],
        ultra_rare=True,
        return_reference=True,
    )

    assert result == _where(
        "(  fa.family_id in (  'f1'  )  )",
        "(  pi.item in (  'f1.dad'  )  )",
        "BITAND(inheritance_in_members, 4) <> 0",
        "BITAND(allele_in_roles, 128) <> 0",
        "BITAND(allele_in_sexes, 1) <> 0",
        "BITAND(allele_in_statuses, 2) <> 0",
        "BITAND(variant_type, 1) <> 0",
        "(sa.af_allele_freq <= 1.0)",
        "fa.family_id = 'x'",
        "(sa.af_allele_freq >= 0.5)",
        "(sa.af_allele_count <= 1 or sa.af_allele_count is null)",
    )


@pytest.fixture
def frequency_coding_builder(families: FamiliesData) -> FamilyQueryBuilder:
    return _family_builder(
        families,
        extra_variant_columns=("frequency_bin", "coding_bin"),
        extra_properties={
            "rare_boundary": 5,
            "coding_effect_types": ["missense"],
        },
    )


def _fragment_of(where: str, column: str) -> str:
    """Return the one fragment of ``where`` on ``column``, unwrapped."""
    fragments = [
        f.strip() for f in where.split(SEPARATOR)
        if f.lstrip().startswith(f"( {column}")
    ]
    assert len(fragments) == 1, where
    return fragments[0].removeprefix("( ").removesuffix(" )")


def test_where_string_passes_inheritance_to_frequency_bin_heuristic(
    frequency_coding_builder: FamilyQueryBuilder,
) -> None:
    result = frequency_coding_builder._build_where_string(
        inheritance="denovo", return_reference=True)

    assert _fragment_of(result, "fa.frequency_bin") == (
        "fa.frequency_bin IN (0)")


def test_where_string_passes_ultra_rare_to_frequency_bin_heuristic(
    frequency_coding_builder: FamilyQueryBuilder,
) -> None:
    result = frequency_coding_builder._build_where_string(
        ultra_rare=True, return_reference=True)

    fragment = _fragment_of(result, "fa.frequency_bin")
    assert _bins_of(fragment, "fa.frequency_bin") == {"0", "1"}


def test_where_string_passes_frequency_filter_to_frequency_bin_heuristic(
    frequency_coding_builder: FamilyQueryBuilder,
) -> None:
    result = frequency_coding_builder._build_where_string(
        frequency_filter=[("af_allele_freq", (None, 1.0))],
        return_reference=True)

    fragment = _fragment_of(result, "fa.frequency_bin")
    assert _bins_of(fragment, "fa.frequency_bin") == {"0", "1", "2"}


def test_where_string_passes_effect_types_to_coding_heuristic(
    frequency_coding_builder: FamilyQueryBuilder,
) -> None:
    result = frequency_coding_builder._build_where_string(
        effect_types=["missense"], return_reference=True)

    assert result == _where(
        "(  eg.effect_types in (  'missense'  )  )",
        "fa.coding_bin IN (1)",
    )
