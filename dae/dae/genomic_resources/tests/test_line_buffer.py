import pytest

from dae.genomic_resources.genome_position_table import LineBuffer


def test_line_buffer_simple():
    buffer = LineBuffer()
    buffer.append('1', 1435348, 1435664, None)
    buffer.append('1', 1435665, 1435739, None)
    
    assert buffer.region() == ("1", 1435348, 1435739)

    for row in buffer.fetch("1", 1435400, 1435400):
        print(row)
        assert row == ("1", 1435348, 1435664, None)


def test_line_buffer_simple_2():
    buffer = LineBuffer()
    buffer.append('1', 4, 4, "1")
    buffer.append('1', 4, 4, "2")
    buffer.append('1', 5, 5, "3")
    buffer.append('1', 8, 8, "4")

    res = list(buffer.fetch("1", 4, 8))
    assert len(res) == 4

@pytest.mark.parametrize("pos,expected", [
    (1, 4),
    (4, 4),
    (5, 2),
])
def test_line_buffer_prune(pos, expected):
    buffer = LineBuffer()
    buffer.append('1', 4, 4, "1")
    buffer.append('1', 4, 4, "2")
    buffer.append('1', 5, 5, "3")
    buffer.append('1', 8, 8, "4")

    buffer.prune("1", pos)
    assert len(buffer) == expected


@pytest.mark.parametrize("pos,expected", [
    (1, -1),
    (4, 0),
    (5, 2),
    (8, 3),
    (9, 4),
    (10, 4),
    (11, 5),
])
def test_line_buffer_find_index(pos, expected):
    buffer = LineBuffer()
    buffer.append('1', 4, 4, "1")
    buffer.append('1', 4, 4, "2")
    buffer.append('1', 5, 5, "3")
    buffer.append('1', 8, 8, "4")
    buffer.append("1", 9, 10, "5")
    buffer.append("1", 12, 14, "6")

    assert buffer.find_index("1", pos) == expected


def test_line_buffer_simple_3():
    buffer = LineBuffer()
    buffer.append('1',  1, 10, None)
    buffer.append('1', 11, 20, None)
    buffer.append('1', 21, 30, None)
    buffer.append('1', 31, 40, None)
    buffer.append('1', 41, 50, None)
    buffer.append('1', 61, 70, None)

    assert buffer.contains('1', 1)

    res = list(buffer.fetch("1", 1, 1))
    assert len(res) == 1

    assert res[0][:3] == ('1', 1, 10,)
