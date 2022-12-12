# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.genomic_resources.genomic_position_table import Line, LineBuffer


def test_line_buffer_simple():
    buffer = LineBuffer()
    buffer.append(Line("1", 1435348, 1435664, {}, {}))
    buffer.append(Line("1", 1435665, 1435739, {}, {}))

    assert buffer.region() == ("1", 1435348, 1435739)

    for row in buffer.fetch("1", 1435400, 1435400):
        print(row)
        assert row == ("1", 1435348, 1435664)


def test_line_buffer_simple_2():
    buffer = LineBuffer()
    buffer.append(Line("1", 4, 4, {}, {}))
    buffer.append(Line("1", 4, 4, {}, {}))
    buffer.append(Line("1", 5, 5, {}, {}))
    buffer.append(Line("1", 8, 8, {}, {}))

    res = list(buffer.fetch("1", 4, 8))
    assert len(res) == 4


@pytest.mark.parametrize("pos,expected", [
    (1, 5),
    (2, 5),
    (3, 4),
    (4, 4),
    (5, 2),
])
def test_line_buffer_prune(pos, expected):
    buffer = LineBuffer()
    buffer.PRUNE_CUTOFF = 0

    buffer.append(Line("1", 2, 2, {}, {}))
    buffer.append(Line("1", 4, 4, {}, {}))
    buffer.append(Line("1", 4, 4, {}, {}))
    buffer.append(Line("1", 5, 5, {}, {}))
    buffer.append(Line("1", 8, 8, {}, {}))

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
    buffer.append(Line("1", 4, 4, {}, {}))  # 0
    buffer.append(Line("1", 4, 4, {}, {}))  # 1
    buffer.append(Line("1", 5, 5, {}, {}))  # 2
    buffer.append(Line("1", 8, 8, {}, {}))  # 3
    buffer.append(Line("1", 9, 10, {}, {}))  # 4
    buffer.append(Line("1", 12, 14, {}, {}))  # 5

    assert buffer.find_index("1", pos) == expected


def test_line_buffer_simple_3():
    buffer = LineBuffer()
    buffer.append(Line("1", 1, 10, {}, {}))
    buffer.append(Line("1", 11, 20, {}, {}))
    buffer.append(Line("1", 21, 30, {}, {}))
    buffer.append(Line("1", 31, 40, {}, {}))
    buffer.append(Line("1", 41, 50, {}, {}))
    buffer.append(Line("1", 61, 70, {}, {}))

    assert buffer.contains("1", 1)

    res = list(buffer.fetch("1", 1, 1))
    assert len(res) == 1

    assert res[0][:3] == ("1", 1, 10,)


@pytest.mark.parametrize("pos,index", [
    (1847882, 6),
    (1847880, 0),
    (1847881, 3),
    (1847883, 6),
    (1847884, 8),
    (1847885, 11),
])
def test_find_index_buggy(pos, index):
    buffer = LineBuffer()
    buffer.append(Line("1", 1847880, 1847880, {}, {}))  # 0
    buffer.append(Line("1", 1847880, 1847880, {}, {}))  # 1
    buffer.append(Line("1", 1847880, 1847880, {}, {}))  # 2
    buffer.append(Line("1", 1847881, 1847881, {}, {}))  # 3
    buffer.append(Line("1", 1847881, 1847881, {}, {}))  # 4
    buffer.append(Line("1", 1847881, 1847881, {}, {}))  # 5
    buffer.append(Line("1", 1847883, 1847883, {}, {}))  # 6
    buffer.append(Line("1", 1847883, 1847883, {}, {}))  # 7
    buffer.append(Line("1", 1847884, 1847884, {}, {}))  # 8
    buffer.append(Line("1", 1847884, 1847884, {}, {}))  # 9
    buffer.append(Line("1", 1847884, 1847884, {}, {}))  # 10
    buffer.append(Line("1", 1847885, 1847885, {}, {}))  # 11

    assert buffer.find_index("1", pos) == index


def test_find_index_buggy_2():
    buffer = LineBuffer()
    buffer.append(Line("1", 503142, 503143, {}, {}))
    buffer.append(Line("1", 503144, 503144, {}, {}))
    buffer.append(Line("1", 503145, 503145, {}, {}))
    buffer.append(Line("1", 503146, 503146, {}, {}))
    buffer.append(Line("1", 503147, 503148, {"key": "found"}, {}))
    buffer.append(Line("1", 503149, 503158, {}, {}))
    buffer.append(Line("1", 503159, 503159, {}, {}))

    index = buffer.find_index("1", 503148)
    assert index != -1

    print(index, buffer.deque[index])

    lines = list(buffer.fetch("1", 503148, 503148))
    assert len(lines) == 1
    line = lines[0]
    assert line.chrom == "1"
    assert line.pos_begin == 503147
    assert line.pos_end == 503148
    assert line.get("key") == "found"
