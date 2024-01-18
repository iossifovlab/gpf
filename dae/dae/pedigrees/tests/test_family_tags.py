# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Callable

import pytest

from dae.pedigrees.family import FamilyTag, Family
from dae.pedigrees.family_tag_builder import check_tag, \
    tag_nuclear_family, \
    tag_quad_family, \
    tag_trio_family, \
    tag_simplex_family, \
    tag_multiplex_family, \
    tag_control_family, \
    tag_affected_dad_family, \
    tag_affected_mom_family, \
    tag_affected_prb_family, \
    tag_affected_sib_family, \
    tag_unaffected_dad_family, \
    tag_unaffected_mom_family, \
    tag_unaffected_prb_family, \
    tag_unaffected_sib_family, \
    tag_male_prb_family, \
    tag_female_prb_family, \
    tag_missing_mom_family, \
    tag_missing_dad_family, \
    check_family_tags_query
from dae.pedigrees.testing import build_family


@pytest.mark.parametrize(
    "tag,name",
    [
        (FamilyTag.AFFECTED_SIB, "tag_affected_sib_family"),
        (FamilyTag.NUCLEAR, "tag_nuclear_family"),
        (FamilyTag.QUAD, "tag_quad_family"),
        (FamilyTag.TRIO, "tag_trio_family"),
        (FamilyTag.SIMPLEX, "tag_simplex_family"),
        (FamilyTag.MULTIPLEX, "tag_multiplex_family"),
        (FamilyTag.CONTROL, "tag_control_family"),
        (FamilyTag.AFFECTED_DAD, "tag_affected_dad_family"),
        (FamilyTag.AFFECTED_MOM, "tag_affected_mom_family"),
        (FamilyTag.AFFECTED_PRB, "tag_affected_prb_family"),
        (FamilyTag.AFFECTED_SIB, "tag_affected_sib_family"),
        (FamilyTag.UNAFFECTED_DAD, "tag_unaffected_dad_family"),
        (FamilyTag.UNAFFECTED_MOM, "tag_unaffected_mom_family"),
        (FamilyTag.UNAFFECTED_PRB, "tag_unaffected_prb_family"),
        (FamilyTag.UNAFFECTED_SIB, "tag_unaffected_sib_family"),
        (FamilyTag.MALE_PRB, "tag_male_prb_family"),
        (FamilyTag.FEMALE_PRB, "tag_female_prb_family"),
        (FamilyTag.MISSING_MOM, "tag_missing_mom_family"),
        (FamilyTag.MISSING_DAD, "tag_missing_dad_family"),
    ]
)
def test_family_tag(tag: FamilyTag, name: str) -> None:
    assert tag.label == name


@pytest.fixture
def fam1_fixture() -> Family:
    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   2      prb
            f1       s1       d1     m1     1   1      sib
        """)
    return fam


def test_tag_nuclear_family_simple(fam1_fixture: Family) -> None:

    assert tag_nuclear_family(fam1_fixture)

    assert check_tag(fam1_fixture, FamilyTag.NUCLEAR)


def test_tag_quad_family_simple(fam1_fixture: Family) -> None:

    assert tag_quad_family(fam1_fixture)
    assert check_tag(fam1_fixture, FamilyTag.QUAD)


def test_tag_trio_family_simple(fam1_fixture: Family) -> None:

    assert not tag_trio_family(fam1_fixture)
    assert not check_tag(fam1_fixture, FamilyTag.TRIO)


def test_tag_simplex_family_simple(fam1_fixture: Family) -> None:

    assert tag_simplex_family(fam1_fixture)
    assert check_tag(fam1_fixture, FamilyTag.SIMPLEX)


def test_tag_multiplex_family_simple(fam1_fixture: Family) -> None:

    assert not tag_multiplex_family(fam1_fixture)
    assert not check_tag(fam1_fixture, FamilyTag.MULTIPLEX)


def test_tag_multiplex_family() -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   2      prb
            f1       s1       d1     m1     1   2      sib
        """)

    assert tag_multiplex_family(fam)
    assert check_tag(fam, FamilyTag.MULTIPLEX)


def test_tag_control_family_simple(fam1_fixture: Family) -> None:

    assert not tag_control_family(fam1_fixture)
    assert not check_tag(fam1_fixture, FamilyTag.CONTROL)


def test_tag_control_family() -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   1      prb
            f1       s1       d1     m1     1   1      sib
        """)

    assert tag_control_family(fam)
    assert check_tag(fam, FamilyTag.CONTROL)


@pytest.mark.parametrize(
    "tagger,tag,value",
    [
        (tag_affected_dad_family, FamilyTag.AFFECTED_DAD, False),
        (tag_unaffected_dad_family, FamilyTag.UNAFFECTED_DAD, True)
    ]
)
def test_tag_affected_dad_family_simple(
    fam1_fixture: Family,
    tagger: Callable[[Family], bool], tag: FamilyTag, value: bool
) -> None:

    assert tagger(fam1_fixture) == value
    assert check_tag(fam1_fixture, tag) == value


@pytest.mark.parametrize(
    "tagger,tag,value",
    [
        (tag_affected_dad_family, FamilyTag.AFFECTED_DAD, True),
        (tag_unaffected_dad_family, FamilyTag.UNAFFECTED_DAD, False)
    ]
)
def test_tag_affected_dad_family(
    tagger: Callable[[Family], bool], tag: FamilyTag, value: bool
) -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   2      dad
            f1       p1       d1     m1     2   1      prb
            f1       s1       d1     m1     1   1      sib
        """)

    assert tagger(fam) == value
    assert check_tag(fam, tag) == value


@pytest.mark.parametrize(
    "tagger,tag,value",
    [
        (tag_affected_mom_family, FamilyTag.AFFECTED_MOM, False),
        (tag_unaffected_mom_family, FamilyTag.UNAFFECTED_MOM, True)
    ]
)
def test_tag_affected_mom_family_simple(
    fam1_fixture: Family,
    tagger: Callable[[Family], bool], tag: FamilyTag, value: bool
) -> None:

    assert tagger(fam1_fixture) == value
    assert check_tag(fam1_fixture, tag) == value


@pytest.mark.parametrize(
    "tagger,tag,value",
    [
        (tag_affected_mom_family, FamilyTag.AFFECTED_MOM, True),
        (tag_unaffected_mom_family, FamilyTag.UNAFFECTED_MOM, False)
    ]
)
def test_tag_affected_mom_family(
    tagger: Callable[[Family], bool], tag: FamilyTag, value: bool
) -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   2      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   1      prb
            f1       s1       d1     m1     1   1      sib
        """)

    assert tagger(fam) == value
    assert check_tag(fam, tag) == value


@pytest.mark.parametrize(
    "tagger,tag,value",
    [
        (tag_affected_prb_family, FamilyTag.AFFECTED_PRB, True),
        (tag_unaffected_prb_family, FamilyTag.UNAFFECTED_PRB, False)
    ]
)
def test_tag_affected_prb_family_simple(
    fam1_fixture: Family,
    tagger: Callable[[Family], bool], tag: FamilyTag, value: bool
) -> None:

    assert tagger(fam1_fixture) == value
    assert check_tag(fam1_fixture, tag) == value


@pytest.mark.parametrize(
    "tagger,tag,value",
    [
        (tag_affected_prb_family, FamilyTag.AFFECTED_PRB, False),
        (tag_unaffected_prb_family, FamilyTag.UNAFFECTED_PRB, True)
    ]
)
def test_tag_affected_prb_family(
    tagger: Callable[[Family], bool], tag: FamilyTag, value: bool
) -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   2      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   1      prb
            f1       s1       d1     m1     1   1      sib
        """)

    assert tagger(fam) == value
    assert check_tag(fam, tag) == value


@pytest.mark.parametrize(
    "tagger,tag,value",
    [
        (tag_affected_sib_family, FamilyTag.AFFECTED_SIB, False),
        (tag_unaffected_sib_family, FamilyTag.UNAFFECTED_SIB, True)
    ]
)
def test_tag_affected_sib_family_simple(
    fam1_fixture: Family,
    tagger: Callable[[Family], bool], tag: FamilyTag, value: bool
) -> None:

    assert tagger(fam1_fixture) == value
    assert check_tag(fam1_fixture, tag) == value


@pytest.mark.parametrize(
    "tagger,tag,value",
    [
        (tag_affected_sib_family, FamilyTag.AFFECTED_SIB, True),
        (tag_unaffected_sib_family, FamilyTag.UNAFFECTED_SIB, False)
    ]
)
def test_tag_affected_sib_family(
    tagger: Callable[[Family], bool], tag: FamilyTag, value: bool
) -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   1      prb
            f1       s1       d1     m1     1   2      sib
        """)

    assert tagger(fam) == value
    assert check_tag(fam, tag) == value


@pytest.mark.parametrize(
    "tagger,tag,value",
    [
        (tag_affected_sib_family, FamilyTag.AFFECTED_SIB, True),
        (tag_unaffected_sib_family, FamilyTag.UNAFFECTED_SIB, True)
    ]
)
def test_tag_affected_sibs_family(
    tagger: Callable[[Family], bool], tag: FamilyTag, value: bool
) -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   1      prb
            f1       s1       d1     m1     1   1      sib
            f1       s2       d1     m1     1   2      sib
        """)

    assert tagger(fam) == value
    assert check_tag(fam, tag) == value


def test_tag_male_prb_family_simple(fam1_fixture: Family) -> None:

    assert not tag_male_prb_family(fam1_fixture)
    assert not check_tag(fam1_fixture, FamilyTag.MALE_PRB)


def test_tag_male_prb_family() -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     1   2      prb
            f1       s1       d1     m1     1   1      sib
            f1       s2       d1     m1     2   2      sib
        """)

    assert tag_male_prb_family(fam)
    assert check_tag(fam, FamilyTag.MALE_PRB)


def test_tag_female_prb_family_simple(fam1_fixture: Family) -> None:

    assert tag_female_prb_family(fam1_fixture)
    assert check_tag(fam1_fixture, FamilyTag.FEMALE_PRB)


def test_tag_female_prb_family() -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     1   2      prb
            f1       s1       d1     m1     1   1      sib
            f1       s2       d1     m1     2   2      sib
        """)

    assert not tag_female_prb_family(fam)
    assert not check_tag(fam, FamilyTag.FEMALE_PRB)


def test_tag_missing_mom_family_simple(fam1_fixture: Family) -> None:

    assert not tag_missing_mom_family(fam1_fixture)
    assert not check_tag(fam1_fixture, FamilyTag.MISSING_MOM)


def test_tag_missing_mom_family() -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role generated
            f1       m1       0      0      2   1      mom  1
            f1       d1       0      0      1   1      dad  0
            f1       p1       d1     m1     1   2      prb  0
        """)

    assert tag_missing_mom_family(fam)
    assert check_tag(fam, FamilyTag.MISSING_MOM)


def test_tag_missing_mom_family_again() -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       d1       0      0      1   1      dad
            f1       p1       d1     0      1   2      prb
        """)

    assert tag_missing_mom_family(fam)
    assert check_tag(fam, FamilyTag.MISSING_MOM)


def test_tag_missing_dad_family_simple(fam1_fixture: Family) -> None:

    assert not tag_missing_dad_family(fam1_fixture)
    assert not check_tag(fam1_fixture, FamilyTag.MISSING_DAD)


def test_tag_missing_dad_family() -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role generated
            f1       m1       0      0      2   1      mom  0
            f1       d1       0      0      1   1      dad  1
            f1       p1       d1     m1     1   2      prb  0
        """)

    assert tag_missing_dad_family(fam)
    assert check_tag(fam, FamilyTag.MISSING_DAD)


def test_tag_missing_dad_family_again() -> None:

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      1   1      mom
            f1       p1       0      m1     1   2      prb
        """)

    assert tag_missing_dad_family(fam)
    assert check_tag(fam, FamilyTag.MISSING_DAD)


@pytest.mark.parametrize(
    "or_mode,included_tags,excluded_tags,expected",
    [
        (False, {FamilyTag.NUCLEAR}, {}, True),
        (False, {FamilyTag.QUAD}, {}, True),
        (False, {FamilyTag.NUCLEAR, FamilyTag.QUAD}, {}, True),
        (
            False, 
            {FamilyTag.NUCLEAR, FamilyTag.QUAD, FamilyTag.MALE_PRB},
            {},
            False
        ),
        (False, {FamilyTag.NUCLEAR}, {FamilyTag.QUAD}, False),
        (False, {}, {FamilyTag.MISSING_DAD}, True),
        (False, {FamilyTag.NUCLEAR}, {FamilyTag.MISSING_DAD}, True),
        (True, {FamilyTag.QUAD}, {FamilyTag.TRIO}, True),
        (True, {FamilyTag.QUAD}, {}, True),
        (True, {FamilyTag.QUAD, FamilyTag.NUCLEAR}, {}, True),
        (True, {FamilyTag.QUAD}, {FamilyTag.NUCLEAR}, True),
        (True, {}, {FamilyTag.TRIO}, True),
        (True, {}, {FamilyTag.QUAD}, False),
        (True, {FamilyTag.MISSING_DAD}, {FamilyTag.QUAD}, False),
        (
            True, 
            {FamilyTag.NUCLEAR, FamilyTag.QUAD, FamilyTag.MALE_PRB},
            {},
            True
        ),
    ]
)
def test_tag_query(
    fam1_fixture: Family,
    or_mode: bool,
    included_tags: set[FamilyTag],
    excluded_tags: set[FamilyTag],
    expected: bool
) -> None:

    assert tag_nuclear_family(fam1_fixture)
    assert tag_quad_family(fam1_fixture)

    assert check_family_tags_query(
        fam1_fixture,
        or_mode,
        included_tags,
        excluded_tags
    ) == expected
