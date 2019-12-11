from dae.utils.helpers import str2bool


def test_str2bool():

    assert str2bool('True')
    assert not str2bool('False')
