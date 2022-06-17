# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

import pytest

from dae.genomic_resources.genome_position_table import LineBuffer


def test_line_buffer_simple():
    buffer = LineBuffer()
    buffer.append("1", 1435348, 1435664, None)
    buffer.append("1", 1435665, 1435739, None)

    assert buffer.region() == ("1", 1435348, 1435739)

    for row in buffer.fetch("1", 1435400, 1435400):
        print(row)
        assert row == ("1", 1435348, 1435664, None)


def test_line_buffer_simple_2():
    buffer = LineBuffer()
    buffer.append("1", 4, 4, "1")
    buffer.append("1", 4, 4, "2")
    buffer.append("1", 5, 5, "3")
    buffer.append("1", 8, 8, "4")

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

    buffer.append("1", 2, 2, "0")
    buffer.append("1", 4, 4, "1")
    buffer.append("1", 4, 4, "2")
    buffer.append("1", 5, 5, "3")
    buffer.append("1", 8, 8, "4")

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
    buffer.append("1", 4, 4, "1")  # 0
    buffer.append("1", 4, 4, "2")  # 1
    buffer.append("1", 5, 5, "3")  # 2
    buffer.append("1", 8, 8, "4")  # 3
    buffer.append("1", 9, 10, "5")  # 4
    buffer.append("1", 12, 14, "6")  # 5

    assert buffer.find_index("1", pos) == expected


def test_line_buffer_simple_3():
    buffer = LineBuffer()
    buffer.append("1", 1, 10, None)
    buffer.append("1", 11, 20, None)
    buffer.append("1", 21, 30, None)
    buffer.append("1", 31, 40, None)
    buffer.append("1", 41, 50, None)
    buffer.append("1", 61, 70, None)

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
    buffer.append("1", 1847880, 1847880, None)  # 0
    buffer.append("1", 1847880, 1847880, None)  # 1
    buffer.append("1", 1847880, 1847880, None)  # 2
    buffer.append("1", 1847881, 1847881, None)  # 3
    buffer.append("1", 1847881, 1847881, None)  # 4
    buffer.append("1", 1847881, 1847881, None)  # 5
    buffer.append("1", 1847883, 1847883, None)  # 6
    buffer.append("1", 1847883, 1847883, None)  # 7
    buffer.append("1", 1847884, 1847884, None)  # 8
    buffer.append("1", 1847884, 1847884, None)  # 9
    buffer.append("1", 1847884, 1847884, None)  # 10
    buffer.append("1", 1847885, 1847885, None)  # 11

    assert buffer.find_index("1", pos) == index


def test_find_index_buggy_2():
    buffer = LineBuffer()
    # buffer.append("1", 503088, 503088, None)
    # buffer.append("1", 503089, 503089, None)
    # buffer.append("1", 503090, 503090, None)
    # buffer.append("1", 503091, 503091, None)
    # buffer.append("1", 503092, 503092, None)
    # buffer.append("1", 503093, 503093, None)
    # buffer.append("1", 503094, 503094, None)
    # buffer.append("1", 503095, 503095, None)
    # buffer.append("1", 503096, 503096, None)
    # buffer.append("1", 503097, 503097, None)
    # buffer.append("1", 503098, 503098, None)
    # buffer.append("1", 503099, 503099, None)
    # buffer.append("1", 503100, 503100, None)
    # buffer.append("1", 503101, 503102, None)
    # buffer.append("1", 503103, 503103, None)
    # buffer.append("1", 503104, 503104, None)
    # buffer.append("1", 503105, 503105, None)
    # buffer.append("1", 503106, 503106, None)
    # buffer.append("1", 503107, 503110, None)
    # buffer.append("1", 503111, 503114, None)
    # buffer.append("1", 503115, 503116, None)
    # buffer.append("1", 503117, 503117, None)
    # buffer.append("1", 503118, 503118, None)
    # buffer.append("1", 503119, 503119, None)
    # buffer.append("1", 503120, 503120, None)
    # buffer.append("1", 503121, 503121, None)
    # buffer.append("1", 503122, 503122, None)
    # buffer.append("1", 503123, 503124, None)
    # buffer.append("1", 503125, 503125, None)
    # buffer.append("1", 503126, 503126, None)
    # buffer.append("1", 503127, 503127, None)
    # buffer.append("1", 503128, 503129, None)
    # buffer.append("1", 503130, 503130, None)
    # buffer.append("1", 503131, 503131, None)
    # buffer.append("1", 503132, 503132, None)
    # buffer.append("1", 503133, 503134, None)
    # buffer.append("1", 503135, 503135, None)
    # buffer.append("1", 503136, 503137, None)
    # buffer.append("1", 503138, 503138, None)
    # buffer.append("1", 503139, 503139, None)
    # buffer.append("1", 503140, 503140, None)
    # buffer.append("1", 503141, 503141, None)
    buffer.append("1", 503142, 503143, None)
    buffer.append("1", 503144, 503144, None)
    buffer.append("1", 503145, 503145, None)
    buffer.append("1", 503146, 503146, None)
    buffer.append("1", 503147, 503148, "found")
    buffer.append("1", 503149, 503158, None)
    buffer.append("1", 503159, 503159, None)

    index = buffer.find_index("1", 503148)
    assert index != -1

    print(index, buffer.deque[index])

    lines = list(buffer.fetch("1", 503148, 503148))
    assert lines == [
        ("1", 503147, 503148, "found")
    ]
