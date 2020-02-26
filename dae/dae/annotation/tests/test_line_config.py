from dae.annotation.tools.utils import LineMapper


def test_line_config_simple():
    lm = LineMapper(['a', 'b'])
    res = lm.map([1, 2])

    assert len(res) == 2
    assert res['a'] == 1
    assert res['b'] == 2


def test_line_config_multi():
    lm = LineMapper(['a', 'b', 'a', 'b'])
    res = lm.map([1, 2, 3, 4])

    assert len(res) == 4
    assert res['a'] == 1
    assert res['b'] == 2
    assert res['a_2'] == 3
    assert res['b_3'] == 4


def test_line_config_multi2():
    lm = LineMapper(['##a', 'b', 'a', 'b', 'c'])
    res = lm.map([1, 2, 3, 4, 5])

    assert len(res) == 5
    assert res['a'] == 1
    assert res['b'] == 2
    assert res['a_2'] == 3
    assert res['b_3'] == 4
    assert res['c'] == 5
