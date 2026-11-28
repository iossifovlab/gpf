# pylint: disable=C0114,C0116,W0212
import logging
from typing import Any

import pytest

from gpf.pedigrees.families_data import merge_families
from gpf.pedigrees.family import Family, FamilyTag, Person
from gpf.variants.attributes import Role, Sex, Status


def _rec(person_id: str, src: str, **overrides: Any) -> dict[str, Any]:
    defaults: dict[str, dict[str, Any]] = {
        "dad": {"sex": "M", "status": "unaffected", "role": "dad"},
        "mom": {"sex": "F", "status": "unaffected", "role": "mom"},
        "p1": {
            "sex": "M", "status": "affected", "role": "prb",
            "dad_id": "dad", "mom_id": "mom",
        },
        "s1": {
            "sex": "F", "status": "unaffected", "role": "sib",
            "dad_id": "dad", "mom_id": "mom",
        },
    }
    rec: dict[str, Any] = {
        "family_id": "f1",
        "person_id": person_id,
        "src": src,
        **defaults[person_id],
    }
    rec.update(overrides)
    return rec


def _trio(src: str, **p1_overrides: Any) -> Family:
    return Family.from_records([  # type: ignore[arg-type]
        _rec("dad", src),
        _rec("mom", src),
        _rec("p1", src, **p1_overrides),
    ])


def _quad(src: str, **p1_overrides: Any) -> Family:
    return Family.from_records([  # type: ignore[arg-type]
        _rec("dad", src),
        _rec("mom", src),
        _rec("p1", src, **p1_overrides),
        _rec("s1", src),
    ])


def _warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [
        r.getMessage() for r in caplog.records
        if r.levelno == logging.WARNING
    ]


def test_different_family_ids_raise() -> None:
    l_fam = _trio("l")
    r_fam = Family.from_records([  # type: ignore[arg-type]
        _rec("dad", "r", family_id="f2"),
    ])

    with pytest.raises(AssertionError) as excinfo:
        merge_families(l_fam, r_fam)

    assert str(excinfo.value) == (
        "Merging families is only allowed with matching family IDs!"
        " (f1 != f2)")


def test_equal_families_return_the_right_family_object() -> None:
    l_fam = _trio("l")
    r_fam = _trio("r")

    result = merge_families(l_fam, r_fam)

    assert result is r_fam
    assert result.persons["p1"] is r_fam.persons["p1"]


def test_equal_families_ignore_layout_and_other_attributes() -> None:
    l_fam = _trio("l", layout="1:10.0,10.0", extra="left")
    r_fam = _trio("r")

    result = merge_families(l_fam, r_fam)

    assert result is r_fam
    assert result.persons["p1"].layout is None


def test_equal_families_get_no_tags() -> None:
    r_fam = _trio("r")

    result = merge_families(_trio("l"), r_fam)

    assert result.tags == set()


def test_persons_in_one_family_only_stay_in_the_result() -> None:
    l_fam = _trio("l")
    r_fam = Family.from_records([  # type: ignore[arg-type]
        _rec("dad", "r"),
        _rec("mom", "r"),
        _rec("s1", "r"),
    ])

    result = merge_families(l_fam, r_fam)

    assert list(result.persons) == ["dad", "mom", "p1", "s1"]
    assert result.persons["p1"].get_attr("src") == "l"
    assert result.persons["s1"].get_attr("src") == "r"


def test_merged_family_member_index_follows_merged_order() -> None:
    l_fam = _trio("l")
    r_fam = Family.from_records([  # type: ignore[arg-type]
        _rec("s1", "r"),
        _rec("dad", "r"),
        _rec("mom", "r"),
    ])

    result = merge_families(l_fam, r_fam)

    assert {
        pid: p.member_index for pid, p in result.persons.items()
    } == {"dad": 0, "mom": 1, "p1": 2, "s1": 3}


def test_merged_family_has_new_person_objects() -> None:
    l_fam = _trio("l")
    r_fam = _quad("r")

    result = merge_families(l_fam, r_fam)

    for pid, person in result.persons.items():
        assert person is not r_fam.persons[pid]
        assert person is not l_fam.persons.get(pid)
    assert r_fam.persons["s1"].member_index == 3


def test_merged_family_gets_layout() -> None:
    result = merge_families(_trio("l"), _quad("r"))

    assert all(p.layout is not None for p in result.persons.values())


def test_merged_family_gets_tags() -> None:
    result = merge_families(_trio("l"), _quad("r"))

    assert result.tags == {
        FamilyTag.NUCLEAR,
        FamilyTag.QUAD,
        FamilyTag.SIMPLEX,
        FamilyTag.AFFECTED_PRB,
        FamilyTag.UNAFFECTED_DAD,
        FamilyTag.UNAFFECTED_MOM,
        FamilyTag.UNAFFECTED_SIB,
        FamilyTag.MALE_PRB,
    }


@pytest.mark.parametrize("flag", ["generated", "missing"])
def test_generated_or_missing_left_person_gives_right_person(
    flag: str, caplog: pytest.LogCaptureFixture,
) -> None:
    l_fam = _trio("l", sex="F", **{flag: True})
    r_fam = _quad("r")

    with caplog.at_level(logging.WARNING):
        result = merge_families(l_fam, r_fam, forced=False)

    assert result.persons["p1"].get_attr("src") == "r"
    assert result.persons["p1"].sex == Sex.M
    assert _warnings(caplog) == []


@pytest.mark.parametrize("flag", ["generated", "missing"])
def test_generated_or_missing_right_person_gives_left_person(
    flag: str, caplog: pytest.LogCaptureFixture,
) -> None:
    l_fam = _trio("l")
    r_fam = _quad("r", sex="F", **{flag: True})

    with caplog.at_level(logging.WARNING):
        result = merge_families(l_fam, r_fam, forced=False)

    assert result.persons["p1"].get_attr("src") == "l"
    assert result.persons["p1"].sex == Sex.M
    assert _warnings(caplog) == []


def test_not_sequenced_left_person_gives_right_person() -> None:
    l_fam = _trio("l", not_sequenced=True)
    r_fam = _quad("r")

    result = merge_families(l_fam, r_fam)

    assert result.persons["p1"].get_attr("src") == "r"


def test_both_generated_gives_right_person() -> None:
    l_fam = _trio("l", generated=True)
    r_fam = _quad("r", missing=True)

    result = merge_families(l_fam, r_fam)

    assert result.persons["p1"].get_attr("src") == "r"
    assert result.persons["p1"].get_attr("missing") is True


@pytest.mark.parametrize(("l_over", "r_over", "winner"), [
    ({"sex": "unspecified"}, {}, "r"),
    ({}, {"sex": "unspecified"}, "l"),
    ({"status": "unspecified"}, {}, "r"),
    ({}, {"status": "unspecified"}, "l"),
    ({"role": "unknown"}, {}, "r"),
    ({}, {"role": "unknown"}, "l"),
])
def test_unspecified_field_gives_the_other_person(
    l_over: dict[str, str], r_over: dict[str, str], winner: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    l_fam = _trio("l", **l_over)
    r_fam = _quad("r", **r_over)

    with caplog.at_level(logging.WARNING):
        result = merge_families(l_fam, r_fam, forced=False)

    assert result.persons["p1"].get_attr("src") == winner
    assert _warnings(caplog) == []


def test_chain_checks_sex_before_status() -> None:
    l_fam = _trio("l", status="unspecified")
    r_fam = _quad("r", sex="unspecified")

    result = merge_families(l_fam, r_fam, forced=False)

    assert result.persons["p1"].get_attr("src") == "l"
    assert result.persons["p1"].status == Status.unspecified


def test_chain_checks_status_before_role() -> None:
    l_fam = _trio("l", role="unknown")
    r_fam = _quad("r", status="unspecified")

    result = merge_families(l_fam, r_fam, forced=False)

    assert result.persons["p1"].get_attr("src") == "l"
    assert result.persons["p1"].role == Role.unknown


@pytest.mark.parametrize(("l_over", "r_over"), [
    (
        {"sex": "unspecified", "status": "affected"},
        {"sex": "unspecified", "status": "unspecified"},
    ),
    (
        {"status": "unspecified", "role": "prb"},
        {"status": "unspecified", "role": "unknown"},
    ),
    ({"role": "unknown"}, {"role": "unknown"}),
])
def test_left_check_wins_over_right_check_of_same_field(
    l_over: dict[str, str], r_over: dict[str, str],
) -> None:
    l_fam = _trio("l", **l_over)
    r_fam = _quad("r", **r_over)

    result = merge_families(l_fam, r_fam, forced=False)

    assert result.persons["p1"].get_attr("src") == "r"


def test_equal_fields_keep_right_person() -> None:
    result = merge_families(_trio("l"), _quad("r"), forced=False)

    assert result.persons["p1"].get_attr("src") == "r"


def test_match_ignores_parent_ids(
    caplog: pytest.LogCaptureFixture,
) -> None:
    l_fam = _trio("l")
    r_fam = _quad("r", dad_id=None)

    with caplog.at_level(logging.WARNING):
        result = merge_families(l_fam, r_fam, forced=False)

    assert result.persons["p1"].get_attr("src") == "r"
    assert result.persons["p1"].dad_id != "dad"
    assert not any(
        "different definitions" in m for m in _warnings(caplog))


def test_mismatch_forced_logs_and_picks_right_person(
    caplog: pytest.LogCaptureFixture,
) -> None:
    l_fam = _trio("l")
    r_fam = _quad("r", sex="F")
    l_person = l_fam.persons["p1"]
    r_person = r_fam.persons["p1"]

    with caplog.at_level(logging.WARNING):
        result = merge_families(l_fam, r_fam)

    assert result.persons["p1"].get_attr("src") == "r"
    assert result.persons["p1"].sex == Sex.F
    assert _warnings(caplog) == [
        (f"different definitions for person {l_person}: "
         f"{' '.join(l_person.diff(r_person))}"),
        f"second person {r_person} overwrites the first {l_person}",
    ]


def test_mismatch_not_forced_raises_diff_messages() -> None:
    l_fam = _trio("l")
    r_fam = _quad("r", status="unaffected")
    expected = l_fam.persons["p1"].diff(r_fam.persons["p1"])

    with pytest.raises(AssertionError) as excinfo:
        merge_families(l_fam, r_fam, forced=False)

    assert excinfo.value.args == (expected,)


def test_mismatch_not_forced_logs_one_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    l_fam = _trio("l")
    r_fam = _quad("r", role="sib")

    with caplog.at_level(logging.WARNING), pytest.raises(AssertionError):
        merge_families(l_fam, r_fam, forced=False)

    warnings = _warnings(caplog)
    assert len(warnings) == 1
    assert warnings[0].startswith("different definitions for person")


def test_match_check_can_undo_chain_choice(
    caplog: pytest.LogCaptureFixture,
) -> None:
    l_fam = _trio("l")
    r_fam = _quad("r", sex="unspecified", status="unaffected")

    with caplog.at_level(logging.WARNING):
        result = merge_families(l_fam, r_fam)

    assert result.persons["p1"].get_attr("src") == "r"
    assert result.persons["p1"].sex == Sex.unspecified
    assert len(_warnings(caplog)) == 2


def test_not_forced_raises_for_one_of_several_mismatches() -> None:
    l_fam = _quad("l")
    r_fam = Family.from_records([  # type: ignore[arg-type]
        _rec("dad", "r"),
        _rec("mom", "r"),
        _rec("p1", "r", sex="F"),
        _rec("s1", "r", status="affected"),
    ])
    candidates = [
        l_fam.persons[pid].diff(r_fam.persons[pid]) for pid in ["p1", "s1"]
    ]

    with pytest.raises(AssertionError) as excinfo:
        merge_families(l_fam, r_fam, forced=False)

    assert excinfo.value.args[0] in candidates


def test_match_checks_person_family_id() -> None:
    l_fam = _trio("l")
    r_person = Person(**_rec("p1", "r", family_id="f2"))
    r_fam = Family("f1")
    r_fam.persons = {"p1": r_person}
    expected = l_fam.persons["p1"].diff(r_person)

    with pytest.raises(AssertionError) as excinfo:
        merge_families(l_fam, r_fam, forced=False)

    assert excinfo.value.args == (expected,)
    assert any("family_id: f1 != f2" in m for m in expected)
