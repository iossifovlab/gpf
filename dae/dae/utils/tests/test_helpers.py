from dae.utils.helpers import str2bool


def test_str2bool() -> None:

    assert str2bool("True")
    assert not str2bool("False")
