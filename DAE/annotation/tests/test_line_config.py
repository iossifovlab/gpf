from annotation.tools.annotator_config import LineConfig


def test_line_config_simple():
    lc = LineConfig(['a', 'b'])
    res = lc.build([1,2])

    assert len(res) == 2
    assert res['a'] == 1
    assert res['b'] == 2


def test_line_config_multi():
    lc = LineConfig(['a', 'b', 'a', 'b'])
    res = lc.build([1,2,3,4])

    assert len(res) == 4
    assert res['a'] == 1
    assert res['b'] == 2
    assert res['a_2'] == 3
    assert res['b_3'] == 4


def test_line_config_multi2():
    lc = LineConfig(['##a', 'b', 'a', 'b', 'c'])
    res = lc.build([1,2,3,4, 5])

    assert len(res) == 5
    assert res['a'] == 1
    assert res['b'] == 2
    assert res['a_2'] == 3
    assert res['b_3'] == 4
    assert res['c'] == 5
