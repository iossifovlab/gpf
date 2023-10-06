# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pathlib

import pytest
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.family import FamiliesData
from dae.pedigrees.family_tag_builder import FamilyTagsBuilder
from dae.variants.attributes import Sex, Status

from dae.testing import setup_pedigree


@pytest.fixture
def ped_a(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "ped_a" / "ped.ped", textwrap.dedent("""
        familyId  personId  dadId   momId   sex  status  role
        f1        f1.dad    0       0       1    1       dad
        f1        f1.mom    0       0       2    1       mom
        f1        f1.s1     f1.dad  f1.mom  2    1       sib
        f1        f1.p1     f1.dad  f1.mom  1    2       prb
        """)
    )
    return FamiliesLoader(str(ped_path)).load()


@pytest.fixture
def ped_b(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "ped_b" / "ped.ped", textwrap.dedent("""
        familyId  personId  dadId  momId  sex  status  role
        f1        f1.dad    0      0      1    1       dad
        f1        f1.mom    0      0      2    1       mom
        f1        f1.s2     f1.dad f1.mom 2    2       sib
        """)
    )
    return FamiliesLoader(str(ped_path)).load()


@pytest.fixture
def ped_c(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "ped_c" / "ped.ped", textwrap.dedent("""
        familyId  personId  dadId  momId  sex  status  role
        f1        f1.dad    0      0      1    1       dad
        f1        f1.mom    0      0      2    1       mom
        f1        f1.s1     f1.dad f1.mom 2    1       prb
        f1        f1.s2     f1.dad f1.mom 2    2       sib
        """)
    )
    return FamiliesLoader(str(ped_path)).load()


@pytest.fixture
def ped_d(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "ped_d" / "ped.ped", textwrap.dedent("""
        familyId  personId  dadId  momId  sex  status  role
        f1        f1.dad    0      0      1    1       dad
        f1        f1.mom    0      0      2    1       mom
        f1        f1.s1     f1.dad f1.mom 1    1       sib
        f1        f1.s2     f1.dad f1.mom 2    2       sib
        """)
    )
    return FamiliesLoader(str(ped_path)).load()


@pytest.fixture
def ped_e(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "ped_e" / "ped.ped", textwrap.dedent("""
familyId  personId  dadId  momId  sex  status  role
f1        f1.dad    0      0      1    1       dad
f1        f1.mom    0      0      2    1       mom
f1        f1.s1     f1.dad f1.mom 0    1       sib
f1        f1.s2     f1.dad f1.mom 2    2       sib
        """)
    )
    return FamiliesLoader(str(ped_path)).load()


@pytest.fixture
def ped_f(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "ped_a" / "ped.ped", textwrap.dedent("""
        familyId  personId  dadId   momId   sex  status  role
        f2        f2.dad    0       0       1    1       dad
        f2        f2.mom    0       0       2    1       mom
        f2        f2.p1     f2.dad  f2.mom  1    2       prb
        """)
    )
    return FamiliesLoader(str(ped_path)).load()


@pytest.fixture
def ped_g(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "ped_a" / "ped.ped", textwrap.dedent("""
        familyId  personId  dadId   momId   sex  status  role
        f1        f1.dad    0       0       1    1       dad
        f1        f1.mom    0       0       2    1       mom
        f1        f1.s1     f1.dad  f1.mom  2    1       sib
        f1        f1.p1     f1.dad  f1.mom  1    2       prb
        f3        f3.dad    0       0       1    1       dad
        f3        f3.mom    0       0       2    1       mom
        f3        f3.s1     f3.dad  f3.mom  2    1       sib
        f3        f3.p1     f3.dad  f3.mom  1    2       prb
        """)
    )
    return FamiliesLoader(str(ped_path)).load()


def test_combine_families(ped_a: FamiliesData, ped_b: FamiliesData) -> None:
    new_families = FamiliesData.combine(
        ped_a,
        ped_b,
        forced=False
    )

    merged_f1 = new_families["f1"]
    assert set(merged_f1.persons.keys()) == {
        "f1.mom",
        "f1.dad",
        "f1.p1",
        "f1.s1",
        "f1.s2",
    }


def test_combine_families_role_mismatch(
    ped_a: FamiliesData,
    ped_c: FamiliesData
) -> None:
    with pytest.raises(AssertionError):
        FamiliesData.combine(
            ped_a,
            ped_c,
            forced=False
        )


def test_combine_families_sex_mismatch(
    ped_a: FamiliesData,
    ped_d: FamiliesData
) -> None:
    with pytest.raises(AssertionError):
        FamiliesData.combine(
            ped_a,
            ped_d,
            forced=False
        )


def test_combine_families_sex_unspecified_mismatch(
    ped_a: FamiliesData,
    ped_e: FamiliesData
) -> None:

    new_families = FamiliesData.combine(
        ped_a,
        ped_e,
        forced=False,
    )

    merged_f1 = new_families["f1"]
    assert set(merged_f1.persons.keys()) == {
        "f1.mom",
        "f1.dad",
        "f1.p1",
        "f1.s1",
        "f1.s2",
    }


@pytest.fixture
def ped_gen_and_not_sequenced(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "ped_a" / "ped.ped", textwrap.dedent("""
familyId  personId  dadId   momId   sex  status  role not_sequenced generated
f1        f1.dad    0       0       1    1       dad  False         False
f1        f1.mom    0       0       2    1       mom  False         False
f1        f1.s2     f1.dad  f1.mom  2    1       sib  False         False
f1        f1.p1     f1.dad  f1.mom  1    2       prb  False         False
f1        f1.s3     f1.dad  f1.mom  0    0       sib  True          False
f1        f1.s4     f1.dad  f1.mom  0    0       sib  True          True
        """)
    )
    return FamiliesLoader(str(ped_path)).load()


def test_generated_and_missing_persons(
    ped_gen_and_not_sequenced: FamiliesData
) -> None:
    p_s3 = ped_gen_and_not_sequenced.persons[("f1", "f1.s3")]
    assert p_s3.missing
    assert not p_s3.generated

    p_s4 = ped_gen_and_not_sequenced.persons[("f1", "f1.s4")]
    assert p_s4.missing
    assert p_s4.generated


def test_combine_families_generated_and_missing(
    ped_a: FamiliesData,
    ped_gen_and_not_sequenced: FamiliesData
) -> None:

    new_families = FamiliesData.combine(
        ped_a,
        ped_gen_and_not_sequenced,
        forced=False,
    )

    p_s3 = new_families.persons[("f1", "f1.s3")]
    assert p_s3.missing
    assert not p_s3.generated

    p_s4 = new_families.persons[("f1", "f1.s4")]
    assert p_s4.missing
    assert p_s4.generated


def test_combine_families_creates_copy(
    ped_a: FamiliesData, ped_f: FamiliesData, ped_g: FamiliesData
) -> None:
    new_families = FamiliesData.combine(
        ped_a,
        ped_f,
        forced=True
    )
    new_families = FamiliesData.combine(
        new_families,
        ped_g,
        forced=True
    )

    new_families["f2"].persons["f2.dad"].set_attr("test", "asdf")
    print(ped_f["f2"].persons["f2.dad"]._attributes)
    new_families["f1"].persons["f1.dad"].set_attr("test", "asdf")
    print(ped_a["f1"].persons["f1.dad"]._attributes)

    builder = FamilyTagsBuilder()

    builder.tag_families_data(new_families)

    # assert new_families["f1"].persons["f1.dad"].get_attr(
    #     "tag_family_type"
    # ) is not None
    # assert len(ped_a["f1"].tags.intersection(["tag_family_type"])) == 0
    # assert len(ped_f["f2"].tags.intersection(["tag_family_type"])) == 0
    # assert len(ped_g["f1"].tags.intersection(["tag_family_type"])) == 0
    # assert ped_a["f1"].persons["f1.dad"] \
    #     .get_attr("tag_family_type") is None
    # assert ped_f["f2"].persons["f2.dad"] \
    #     .get_attr("tag_family_type") is None
    # assert ped_g["f1"].persons["f1.dad"] \
    #     .get_attr("tag_family_type") is None
    # assert ped_g["f3"].persons["f3.dad"] \
    #     .get_attr("tag_family_type") is None


@pytest.fixture
def ped_f1_all(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "ped_a" / "ped.ped", textwrap.dedent("""
        familyId  personId  dadId   momId   sex  status  role
        f1        f1.dad    0       0       1    1       dad
        f1        f1.mom    0       0       2    1       mom
        f1        f1.s2     f1.dad  f1.mom  2    1       sib
        f1        f1.p1     f1.dad  f1.mom  1    2       prb
        f1        f1.s3     f1.dad  f1.mom  1    1       sib
        f1        f1.s4     f1.dad  f1.mom  2    1       sib
        """)
    )
    return FamiliesLoader(str(ped_path)).load()


def test_combine_missing(
    ped_gen_and_not_sequenced: FamiliesData, ped_f1_all: FamiliesData
) -> None:
    combined1 = FamiliesData.combine(
        ped_gen_and_not_sequenced,
        ped_f1_all,
        forced=True
    )
    person = combined1.persons[("f1", "f1.s3")]
    assert not person.missing
    assert not person.generated
    assert person.sex == Sex.male
    assert person.status == Status.unaffected

    person = combined1.persons[("f1", "f1.s4")]
    assert not person.missing
    assert not person.generated
    assert person.sex == Sex.female
    assert person.status == Status.unaffected

    combined2 = FamiliesData.combine(
        ped_f1_all,
        ped_gen_and_not_sequenced,
        forced=True
    )

    person = combined2.persons[("f1", "f1.s3")]
    assert not person.missing
    assert not person.generated
    assert person.sex == Sex.male
    assert person.status == Status.unaffected

    person = combined2.persons[("f1", "f1.s4")]
    assert not person.missing
    assert not person.generated
    assert person.sex == Sex.female
    assert person.status == Status.unaffected
