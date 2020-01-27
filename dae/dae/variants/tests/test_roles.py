import pytest

from dae.variants.attributes import Role


@pytest.mark.parametrize('name,role', [
    ('prb', Role.prb),
    ('proband', Role.prb),
    ('Maternal Grandmother', Role.maternal_grandmother),
    ('Father', Role.dad),
    ('mother', Role.mom),
])
def test_roles_simple(name, role):

    assert Role.from_name(name) == role
