# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.genomic_resources.repository import (
    is_version_constraint_satisfied,
    parse_gr_id_version_token,
)


def test_parse_gr_id_version_token() -> None:
    with pytest.raises(ValueError, match="unexpected value for resource ID"):
        parse_gr_id_version_token("aaa(3.")

    with pytest.raises(ValueError, match="unexpected value for resource ID"):
        parse_gr_id_version_token("aaa(3.a)")
    with pytest.raises(ValueError, match="unexpected value for resource ID"):
        parse_gr_id_version_token("(3.2)")
    with pytest.raises(ValueError, match="unexpected value for resource ID"):
        parse_gr_id_version_token("aa*(3.0)")
    with pytest.raises(ValueError, match="unexpected value for resource ID"):
        parse_gr_id_version_token("aa(0)")
    with pytest.raises(ValueError, match="unexpected value for resource ID"):
        parse_gr_id_version_token("aa(0.2.3)")

    assert parse_gr_id_version_token("aa") == ("aa", (0,))
    assert parse_gr_id_version_token("aa(2)") == ("aa", (2,))
    assert parse_gr_id_version_token("aa(2.2.4.1)") == ("aa", (2, 2, 4, 1))


def test_is_version_constraint_satisfied() -> None:
    assert is_version_constraint_satisfied(None, (0,))
    assert is_version_constraint_satisfied(None, (1, 2))

    assert is_version_constraint_satisfied("1.2", (1, 2))
    assert is_version_constraint_satisfied("1.2", (1, 3))
    assert is_version_constraint_satisfied("1.2", (1, 2, 1))
    assert not is_version_constraint_satisfied("1.2", (1, 1))

    assert is_version_constraint_satisfied(">=1.2", (1, 2))
    assert is_version_constraint_satisfied(">=1.2", (1, 3))
    assert is_version_constraint_satisfied(">=1.2", (1, 2, 1))
    assert not is_version_constraint_satisfied(">=1.2", (1, 1))

    assert is_version_constraint_satisfied("=1.2", (1, 2))
    assert not is_version_constraint_satisfied("=1.2", (1, 3))
    assert not is_version_constraint_satisfied("=1.2", (1, 2, 1))
    assert not is_version_constraint_satisfied("=1.2", (1, 1))
