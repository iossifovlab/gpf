# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.variants.attributes import Role


@pytest.mark.parametrize(
    "name,role",
    [
        ("prb", Role.prb),
        ("proband", Role.prb),
        ("Maternal Grandmother", Role.maternal_grandmother),
        ("Father", Role.dad),
        ("mother", Role.mom),
        ("Younger sibling", Role.sib),
        ("Older sibling", Role.sib),
    ],
)
def test_roles_simple(name: str, role: Role) -> None:

    assert Role.from_name(name) == role
