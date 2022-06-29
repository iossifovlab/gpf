# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

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
    tag_male_prb_family, \
    tag_female_prb_family, \
    tag_missing_mom_family, \
    tag_missing_dad_family
from dae.pedigrees.testing import build_family


@pytest.fixture
def fam1_fixture():
    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   2      prb
            f1       s1       d1     m1     1   1      sib
        """)
    return fam


def test_tag_nuclear_family_simple(fam1_fixture):

    assert tag_nuclear_family(fam1_fixture)

    assert check_tag(fam1_fixture, "tag_nuclear_family", True)


def test_tag_quad_family_simple(fam1_fixture):

    assert tag_quad_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_quad_family", True)


def test_tag_trio_family_simple(fam1_fixture):

    assert not tag_trio_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_trio_family", False)


def test_tag_simplex_family_simple(fam1_fixture):

    assert tag_simplex_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_simplex_family", True)


def test_tag_multiplex_family_simple(fam1_fixture):

    assert not tag_multiplex_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_multiplex_family", False)


def test_tag_multiplex_family():

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   2      prb
            f1       s1       d1     m1     1   2      sib
        """)

    assert tag_multiplex_family(fam)
    assert check_tag(fam, "tag_multiplex_family", True)


def test_tag_control_family_simple(fam1_fixture):

    assert not tag_control_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_control_family", False)


def test_tag_control_family():

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   1      prb
            f1       s1       d1     m1     1   1      sib
        """)

    assert tag_control_family(fam)
    assert check_tag(fam, "tag_control_family", True)


def test_tag_affected_dad_family_simple(fam1_fixture):

    assert not tag_affected_dad_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_affected_dad_family", False)


def test_tag_affected_dad_family():

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   2      dad
            f1       p1       d1     m1     2   1      prb
            f1       s1       d1     m1     1   1      sib
        """)

    assert tag_affected_dad_family(fam)
    assert check_tag(fam, "tag_affected_dad_family", True)


def test_tag_affected_mom_family_simple(fam1_fixture):

    assert not tag_affected_mom_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_affected_mom_family", False)


def test_tag_affected_mom_family():

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   2      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   1      prb
            f1       s1       d1     m1     1   1      sib
        """)

    assert tag_affected_mom_family(fam)
    assert check_tag(fam, "tag_affected_mom_family", True)


def test_tag_affected_prb_family_simple(fam1_fixture):

    assert tag_affected_prb_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_affected_prb_family", True)


def test_tag_affected_prb_family():

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   2      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   1      prb
            f1       s1       d1     m1     1   1      sib
        """)

    assert not tag_affected_prb_family(fam)
    assert check_tag(fam, "tag_affected_prb_family", False)


def test_tag_affected_sib_family_simple(fam1_fixture):

    assert not tag_affected_sib_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_affected_sib_family", False)


def test_tag_affected_sib_family():

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   1      prb
            f1       s1       d1     m1     1   1      sib
            f1       s2       d1     m1     1   2      sib
        """)

    assert tag_affected_sib_family(fam)
    assert check_tag(fam, "tag_affected_sib_family", True)


def test_tag_male_prb_family_simple(fam1_fixture):

    assert not tag_male_prb_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_male_prb_family", False)


def test_tag_male_prb_family():

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
    assert check_tag(fam, "tag_male_prb_family", True)


def test_tag_female_prb_family_simple(fam1_fixture):

    assert tag_female_prb_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_female_prb_family", True)


def test_tag_female_prb_family():

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
    assert check_tag(fam, "tag_female_prb_family", False)


def test_tag_missing_mom_family_simple(fam1_fixture):

    assert not tag_missing_mom_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_missing_mom_family", False)


def test_tag_missing_mom_family():

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role generated
            f1       m1       0      0      2   1      mom  1
            f1       d1       0      0      1   1      dad  0
            f1       p1       d1     m1     1   2      prb  0
        """)

    assert tag_missing_mom_family(fam)
    assert check_tag(fam, "tag_missing_mom_family", True)


def test_tag_missing_mom_family_again():

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       d1       0      0      1   1      dad
            f1       p1       d1     0      1   2      prb
        """)

    assert tag_missing_mom_family(fam)
    assert check_tag(fam, "tag_missing_mom_family", True)


def test_tag_missing_dad_family_simple(fam1_fixture):

    assert not tag_missing_dad_family(fam1_fixture)
    assert check_tag(fam1_fixture, "tag_missing_dad_family", False)


def test_tag_missing_dad_family():

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role generated
            f1       m1       0      0      2   1      mom  0
            f1       d1       0      0      1   1      dad  1
            f1       p1       d1     m1     1   2      prb  0
        """)

    assert tag_missing_dad_family(fam)
    assert check_tag(fam, "tag_missing_dad_family", True)


def test_tag_missing_dad_family_again():

    fam = build_family(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      1   1      mom
            f1       p1       0      m1     1   2      prb
        """)

    assert tag_missing_dad_family(fam)
    assert check_tag(fam, "tag_missing_dad_family", True)
