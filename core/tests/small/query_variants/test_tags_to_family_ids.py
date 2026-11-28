# pylint: disable=W0621,C0114,C0116
from types import SimpleNamespace
from typing import cast

import pytest

from gpf.pedigrees.families_data import FamiliesData, tag_families_data
from gpf.pedigrees.testing import build_families_data
from gpf.query_variants.base_query_variants import QueryVariants
from gpf.query_variants.sql.schema2.sql_query_builder import TagsQuery

PEDIGREE = """
    familyId personId dadId  momId  sex status role
    f1       m1       0      0      2   1      mom
    f1       d1       0      0      1   1      dad
    f1       p1       d1     m1     2   2      prb
    f1       s1       d1     m1     1   1      sib
    f2       m2       0      0      2   1      mom
    f2       d2       0      0      1   1      dad
    f2       p2       d2     m2     1   2      prb
"""


@pytest.fixture
def untagged_families() -> FamiliesData:
    return build_families_data(PEDIGREE)


@pytest.fixture
def tagged_families() -> FamiliesData:
    families = build_families_data(PEDIGREE)
    tag_families_data(families)
    return families


def tags_to_family_ids(
    families: FamiliesData,
    tags_query: TagsQuery | None,
) -> set[str] | None:
    """Call the function unbound, as ``RawFamilyVariants`` does."""
    holder = cast(QueryVariants, SimpleNamespace(families=families))
    return QueryVariants.tags_to_family_ids(holder, tags_query)


def test_none_query_returns_none(tagged_families: FamiliesData) -> None:
    result = tags_to_family_ids(tagged_families, None)

    assert result is None


def test_default_argument_returns_none(
    tagged_families: FamiliesData,
) -> None:
    holder = cast(QueryVariants, SimpleNamespace(families=tagged_families))

    result = QueryVariants.tags_to_family_ids(holder)

    assert result is None


@pytest.mark.parametrize("or_mode", [False, True])
def test_query_without_tags_returns_none(
    tagged_families: FamiliesData,
    or_mode: bool,
) -> None:
    query = TagsQuery(tags_or_mode=or_mode)

    result = tags_to_family_ids(tagged_families, query)

    assert result is None


def test_selected_tag_returns_matching_family(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(selected_family_tags=["tag_quad_family"])

    result = tags_to_family_ids(tagged_families, query)

    assert result == {"f1"}


def test_deselected_tag_excludes_matching_family(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(deselected_family_tags=["tag_quad_family"])

    result = tags_to_family_ids(tagged_families, query)

    assert result == {"f2"}


def test_selected_and_deselected_tags_and_mode(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(
        selected_family_tags=["tag_nuclear_family"],
        deselected_family_tags=["tag_trio_family"],
    )

    result = tags_to_family_ids(tagged_families, query)

    assert result == {"f1"}


def test_and_mode_requires_every_selected_tag(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(
        selected_family_tags=["tag_quad_family", "tag_trio_family"],
    )

    result = tags_to_family_ids(tagged_families, query)

    assert result == set()


def test_or_mode_accepts_any_selected_tag(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(
        selected_family_tags=["tag_quad_family", "tag_trio_family"],
        tags_or_mode=True,
    )

    result = tags_to_family_ids(tagged_families, query)

    assert result == {"f1", "f2"}


def test_or_mode_accepts_family_lacking_a_deselected_tag(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(
        selected_family_tags=["tag_quad_family"],
        deselected_family_tags=["tag_nuclear_family", "tag_quad_family"],
        tags_or_mode=True,
    )

    result = tags_to_family_ids(tagged_families, query)

    assert result == {"f1", "f2"}


def test_or_mode_rejects_family_with_every_deselected_tag_and_no_selected(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(
        selected_family_tags=["tag_quad_family"],
        deselected_family_tags=["tag_nuclear_family", "tag_trio_family"],
        tags_or_mode=True,
    )

    result = tags_to_family_ids(tagged_families, query)

    assert result == {"f1"}


def test_no_passing_family_returns_empty_set(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(deselected_family_tags=["tag_nuclear_family"])

    result = tags_to_family_ids(tagged_families, query)

    assert result == set()


def test_empty_selected_list_returns_every_family(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(selected_family_tags=[])

    result = tags_to_family_ids(tagged_families, query)

    assert result == {"f1", "f2"}


def test_empty_selected_list_in_or_mode_returns_empty_set(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(selected_family_tags=[], tags_or_mode=True)

    result = tags_to_family_ids(tagged_families, query)

    assert result == set()


def test_unknown_selected_label_raises_key_error(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(selected_family_tags=["no_such_tag"])

    with pytest.raises(KeyError, match="no_such_tag"):
        tags_to_family_ids(tagged_families, query)


def test_unknown_deselected_label_raises_key_error(
    tagged_families: FamiliesData,
) -> None:
    query = TagsQuery(deselected_family_tags=["no_such_tag"])

    with pytest.raises(KeyError, match="no_such_tag"):
        tags_to_family_ids(tagged_families, query)


def test_untagged_families_match_no_selected_tag(
    untagged_families: FamiliesData,
) -> None:
    query = TagsQuery(selected_family_tags=["tag_quad_family"])

    result = tags_to_family_ids(untagged_families, query)

    assert result == set()


def test_untagged_families_all_pass_a_deselected_tag(
    untagged_families: FamiliesData,
) -> None:
    query = TagsQuery(deselected_family_tags=["tag_quad_family"])

    result = tags_to_family_ids(untagged_families, query)

    assert result == {"f1", "f2"}
