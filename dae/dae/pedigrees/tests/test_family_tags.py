# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.pedigrees.family_tags import FamilyTagsBuilder
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

    tagger = FamilyTagsBuilder(fam1_fixture)
    assert tagger.tag_nuclear_family()

    assert tagger.check_tag("tag_nuclear_family", True)


def test_tag_quad_family_simple(fam1_fixture):

    tagger = FamilyTagsBuilder(fam1_fixture)
    assert tagger.tag_quad_family()

    assert tagger.check_tag("tag_quad_family", True)


def test_tag_trio_family_simple(fam1_fixture):

    tagger = FamilyTagsBuilder(fam1_fixture)
    assert not tagger.tag_trio_family()

    assert tagger.check_tag("tag_trio_family", False)


def test_tag_simplex_family_simple(fam1_fixture):

    tagger = FamilyTagsBuilder(fam1_fixture)
    assert tagger.tag_simplex_family()

    assert tagger.check_tag("tag_simplex_family", True)


def test_tag_multiplex_family_simple(fam1_fixture):

    tagger = FamilyTagsBuilder(fam1_fixture)
    assert not tagger.tag_multiplex_family()

    assert tagger.check_tag("tag_multiplex_family", False)
