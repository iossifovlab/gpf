# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.genomic_resources.genome_position_table import \
    TabixGenomicPositionTable, \
    open_genome_position_table

from dae.genomic_resources.testing import \
    build_test_resource, \
    tabix_to_resource
from dae.testing import convert_to_tab_separated


def test_default_setup():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem""",
        "data.mem": convert_to_tab_separated("""
            chrom pos_begin pos2  c2
            1     10        12    3.14
            1     11        11    4.14
            1     12        10    5.14""")})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 1
    assert tab.pos_end_column_i == 1
    assert tab.get_special_column_index("chrom") == 0
    assert tab.get_special_column_index("pos_begin") == 1
    assert tab.get_special_column_index("pos_end") == 1


def test_regions():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem""",
        "data.mem": convert_to_tab_separated("""
            chrom pos_begin pos_end  c2
            1     10        12       3.14
            1     15        20       4.14
            1     21        30       5.14""")})

    tab = open_genome_position_table(
        res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 1
    assert tab.pos_end_column_i == 2
    assert list(tab.get_all_records()) == [
        ("1", "10", "12", "3.14"),
        ("1", "15", "20", "4.14"),
        ("1", "21", "30", "5.14")
    ]
    assert list(tab.get_records_in_region("1", 11, 11)) == [
        ("1", "10", "12", "3.14")
    ]

    assert not list(tab.get_records_in_region("1", 13, 14))

    assert list(tab.get_records_in_region("1", 18, 21)) == [
        ("1", "15", "20", "4.14"),
        ("1", "21", "30", "5.14")
    ]


@pytest.mark.parametrize("jump_threshold", [
    0,
    1,
    2,
    1500,
])
def test_regions_in_tabix(tmp_path, tabix_file, jump_threshold):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz""",
        })
    assert res

    tabix_to_resource(
        tabix_file(
            """
            #chrom pos_begin pos_end  c2
            1     10        12       3.14
            1     15        20       4.14
            1     21        30       5.14
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz"
    )

    tab = open_genome_position_table(res, res.config["tabix_table"])
    assert tab
    tab.jump_threshold = jump_threshold

    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 1
    assert tab.pos_end_column_i == 2
    assert list(tab.get_all_records()) == [
        ("1", "10", "12", "3.14"),
        ("1", "15", "20", "4.14"),
        ("1", "21", "30", "5.14")
    ]
    assert list(tab.get_records_in_region("1", 11, 11)) == [
        ("1", "10", "12", "3.14")
    ]

    assert not list(tab.get_records_in_region("1", 13, 14))

    assert list(tab.get_records_in_region("1", 18, 21)) == [
        ("1", "15", "20", "4.14"),
        ("1", "21", "30", "5.14")
    ]


def test_last_call_is_updated(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz""",
        })
    assert res

    tabix_to_resource(
        tabix_file(
            """
            #chrom pos_begin pos_end  c2
            1     10        12       3.14
            1     15        20       4.14
            1     21        30       5.14
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz"
    )

    tab = open_genome_position_table(res, res.config["tabix_table"])
    assert tab._last_call == ("", -1, -1)

    assert list(tab.get_records_in_region("1", 11, 11)) == [
        ("1", "10", "12", "3.14")
    ]
    assert tab._last_call == ("1", 11, 11)

    assert not list(tab.get_records_in_region("1", 13, 14))
    assert tab._last_call == ("1", 13, 14)

    assert list(tab.get_records_in_region("1", 18, 21)) == [
        ("1", "15", "20", "4.14"),
        ("1", "21", "30", "5.14")
    ]
    assert tab._last_call == ("1", 18, 21)


def test_chr_add_pref():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                chrom_mapping:
                    add_prefix: chr""",
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin pos2  c2
            1     10        12    3.14
            X     11        11    4.14
            11    12        10    5.14
            """)})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.get_chromosomes() == ["chr1", "chr11", "chrX"]


def test_chr_del_pref():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                chrom_mapping:
                    del_prefix: chr""",
        "data.mem": """
            chrom    pos_begin pos2  c2
            chr1     10        12    3.14
            chr22    11        11    4.14
            chrX     12        10    5.14"""})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.get_chromosomes() == ["1", "22", "X"]


def test_chrom_mapping_file():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                chrom_mapping:
                    filename: chrom_map.txt""",
        "data.mem": convert_to_tab_separated("""
            chrom    pos_begin pos2  c2
            chr1     10        12    3.14
            chr22    11        11    4.14
            chrX     12        10    5.14"""),
        "chrom_map.txt": convert_to_tab_separated("""
            chrom   file_chrom
            gosho   chr1
            pesho   chr22
        """)})
    tab = open_genome_position_table(
        res, res.config["table"])

    assert tab.get_chromosomes() == ["gosho", "pesho"]
    assert list(tab.get_all_records()) == [
        ("gosho", "10", "12", "3.14"),
        ("pesho", "11", "11", "4.14")
    ]
    assert list(tab.get_records_in_region("pesho")) == [
        ("pesho", "11", "11", "4.14"),
    ]


def test_chrom_mapping_file_with_tabix(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz
                    chrom_mapping:
                        filename: chrom_map.txt""",
            "chrom_map.txt": convert_to_tab_separated("""
                    chrom   file_chrom
                    gosho   chr1
                    pesho   chr22
            """)})

    tabix_to_resource(
        tabix_file(
            """
            #chrom   pos_begin  pos2   c2
            chr1     10         12     3.14
            chr22    11         11     4.14
            chrX     12         14     5.14
            """,
            seq_col=0, start_col=1, end_col=2),
        res, "data.bgz"
    )

    tab = open_genome_position_table(res, res.config["tabix_table"])

    assert tab.get_chromosomes() == ["gosho", "pesho"]
    assert list(tab.get_all_records()) == [
        ("gosho", "10", "12", "3.14"),
        ("pesho", "11", "11", "4.14")
    ]
    assert list(tab.get_records_in_region("pesho")) == [
        ("pesho", "11", "11", "4.14"),
    ]


def test_invalid_chrom_mapping_file_with_tabix(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz
                    chrom_mapping:
                        filename: chrom_map.txt""",
            "chrom_map.txt": convert_to_tab_separated("""
                    something   else
                    gosho       chr1
                    pesho       chr22
            """)})

    tabix_to_resource(
        tabix_file(
            """
            #chrom   pos_begin  pos2   c2
            chr1     10         12     3.14
            chr22    11         11     4.14
            chrX     12         14     5.14
            """,
            seq_col=0, start_col=1, end_col=2),
        res, "data.bgz"
    )

    with pytest.raises(ValueError) as exception:
        tab = open_genome_position_table(res, res.config["tabix_table"])

    assert str(exception.value) == (
        "The chromosome mapping file chrom_map.txt in resource  "
        "is expected to have the two columns 'chrom' and 'file_chrom'"
    )


def test_column_with_name():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                pos_begin:
                    name: pos2""",
        "data.mem": convert_to_tab_separated(
            """
            chrom pos pos2 c2
            1     10  12   3.14
            1     11  11   4.14
            1     12  14   5.14
            """)
    })
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region("1", 12, 12)) == [
        ("1", "10", "12", "3.14")]


def test_column_with_index():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                pos_begin:
                    index: 2""",
        "data.mem": convert_to_tab_separated("""
            chrom pos pos2  c2
            1     10  12    3.14
            1     11  11    4.14
            1     12  14    5.14""")
    })
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region("1", 12, 12)) == [
        ("1", "10", "12", "3.14")]


def test_no_header():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                header_mode: none
                filename: data.mem
                chrom:
                    index: 0
                pos_begin:
                    index: 2""",
        "data.mem": convert_to_tab_separated("""
            1   10  12  3.14
            1   11  11  4.14
            1   12  14  5.14
            """)
    })
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region("1", 12, 12)) == [
        ("1", "10", "12", "3.14")]


def test_header_in_config():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                header_mode: list
                header: ["chrom", "pos", "pos2", "score"]
                filename: data.mem
                pos_begin:
                    name: pos2""",
        "data.mem": convert_to_tab_separated("""
            1   10  12  3.14
            1   11  11  4.14
            1   12  10  5.14""")})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region("1", 12, 12)) == [
        ("1", "10", "12", "3.14")]


def test_space_in_mem_table():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem""",
        "data.mem": convert_to_tab_separated("""
            chrom pos_begin pos2   c2
            1     10        12     3.14
            1     11        EMPTY  4.14
            1     12        10     5.14""")})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 1
    assert list(tab.get_records_in_region("1", 11, 11)) == [
        ("1", "11", "", "4.14")]


def test_text_table():
    res = build_test_resource(
        content={
            "genomic_resource.yaml": """
                table:
                    filename: data.mem""",
            "data.mem": convert_to_tab_separated("""
                chrom pos_begin c1     c2
                1     3         3.14   aa
                1     4         4.14   bb
                1     4         5.14   cc
                1     5         6.14   dd
                1     8         7.14   ee
                2     3         8.14   ff
                """)
        })

    table = open_genome_position_table(res, res.config["table"])
    assert table.get_column_names() == ("chrom", "pos_begin", "c1", "c2")

    assert list(table.get_all_records()) == [
        ("1", "3", "3.14", "aa"),
        ("1", "4", "4.14", "bb"),
        ("1", "4", "5.14", "cc"),
        ("1", "5", "6.14", "dd"),
        ("1", "8", "7.14", "ee"),
        ("2", "3", "8.14", "ff")
    ]

    assert list(table.get_records_in_region("1", 4, 5)) == [
        ("1", "4", "4.14", "bb"),
        ("1", "4", "5.14", "cc"),
        ("1", "5", "6.14", "dd")
    ]

    assert list(table.get_records_in_region("1", 4, None)) == [
        ("1", "4", "4.14", "bb"),
        ("1", "4", "5.14", "cc"),
        ("1", "5", "6.14", "dd"),
        ("1", "8", "7.14", "ee")
    ]

    assert list(table.get_records_in_region("1", None, 4)) == [
        ("1", "3", "3.14", "aa"),
        ("1", "4", "4.14", "bb"),
        ("1", "4", "5.14", "cc")
    ]

    assert not list(table.get_records_in_region("1", 20, 25))

    assert list(table.get_records_in_region("2", None, None)) == [
        ("2", "3", "8.14", "ff")
    ]

    with pytest.raises(Exception):
        list(table.get_records_in_region("3"))


@pytest.mark.parametrize("jump_threshold", [
    0,
    1,
    2,
    1500,
])
def test_tabix_table(tabix_file, tmp_path, jump_threshold):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                    tabix_table:
                        filename: data.bgz""",
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom pos_begin c1     c2
            1      3         3.14   aa
            1      4         4.14   bb
            1      4         5.14   cc
            1      5         6.14   dd
            1      8         7.14   ee
            2      3         8.14   ff
            """, seq_col=0, start_col=1, end_col=1),
        res, "data.bgz"
    )

    table = open_genome_position_table(res, res.config["tabix_table"])
    assert table.get_column_names() == ("chrom", "pos_begin", "c1", "c2")
    table.jump_threshold = jump_threshold

    assert list(table.get_all_records()) == [
        ("1", "3", "3.14", "aa"),
        ("1", "4", "4.14", "bb"),
        ("1", "4", "5.14", "cc"),
        ("1", "5", "6.14", "dd"),
        ("1", "8", "7.14", "ee"),
        ("2", "3", "8.14", "ff")
    ]

    assert list(table.get_records_in_region("1", 4, 5)) == [
        ("1", "4", "4.14", "bb"),
        ("1", "4", "5.14", "cc"),
        ("1", "5", "6.14", "dd")
    ]

    assert list(table.get_records_in_region("1", 4, None)) == [
        ("1", "4", "4.14", "bb"),
        ("1", "4", "5.14", "cc"),
        ("1", "5", "6.14", "dd"),
        ("1", "8", "7.14", "ee")
    ]

    assert list(table.get_records_in_region("1", None, 4)) == [
        ("1", "3", "3.14", "aa"),
        ("1", "4", "4.14", "bb"),
        ("1", "4", "5.14", "cc")
    ]

    assert not list(table.get_records_in_region("1", 20, 25))

    assert list(table.get_records_in_region("2", None, None)) == [
        ("2", "3", "8.14", "ff")
    ]

    with pytest.raises(Exception):
        list(table.get_records_in_region("3"))


@pytest.fixture
def tabix_table(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz""",
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom pos_begin c1
            1      1         1
            1      2         2
            1      3         3
            1      4         4
            1      5         5
            1      6         6
            1      7         7
            1      8         8
            1      9         9
            1      10        10
            1      11        11
            1      12        12
            """, seq_col=0, start_col=1, end_col=1),
        res, "data.bgz"
    )

    table = open_genome_position_table(res, res.config["tabix_table"])
    return table


@pytest.fixture
def regions_tabix_table(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                text_table:
                    filename: data.mem
                tabix_table:
                    filename: data.bgz""",
            "data.mem": """
            """
        })
    tabix_to_resource(
        tabix_file(
            """
            #chrom pos_begin pos_end  c1
            1      1         5        1
            1      6         10       2
            1      11        15       3
            1      16        20       4
            1      21        25       5
            1      26        30       6
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz"
    )

    table = open_genome_position_table(res, res.config["tabix_table"])
    assert table.chrom_column_i == 0
    assert table.pos_begin_column_i == 1
    assert table.pos_end_column_i == 2

    return table


def test_tabix_table_should_use_sequential(tabix_table):
    table = tabix_table
    assert table.get_column_names() == ("chrom", "pos_begin", "c1")

    assert not table._should_use_sequential("1", 1)
    for row in table.get_records_in_region("1", 1, 1):
        print(row)

    assert not table._should_use_sequential("1", 1)

    assert table._should_use_sequential("1", 2)
    assert table._should_use_sequential("1", 3)

    table.jump_threshold = 0
    assert not table._should_use_sequential("1", 3)


def test_regions_tabix_table_should_use_sequential(regions_tabix_table):
    table = regions_tabix_table
    assert table.get_column_names() == ("chrom", "pos_begin", "pos_end", "c1")

    assert not table._should_use_sequential("1", 1)
    for row in table.get_records_in_region("1", 2, 2):
        print(row)

    assert not table._should_use_sequential("1", 1)
    assert not table._should_use_sequential("1", 6)
    assert table._should_use_sequential("1", 11)
    assert table._should_use_sequential("1", 21)

    table.jump_threshold = 0
    assert not table._should_use_sequential("1", 6)
    assert not table._should_use_sequential("1", 11)
    assert not table._should_use_sequential("1", 21)


def test_tabix_table_jumper_current_position(tabix_table):
    table = tabix_table
    assert table.get_column_names() == ("chrom", "pos_begin", "c1")

    for rec in table.get_records_in_region("1", 1):
        print(rec)
        assert rec[0] == "1"
        assert int(rec[1]) == 1
        break

    for rec in table.get_records_in_region("1", 6):
        assert rec[0] == "1", rec
        assert int(rec[1]) == 6, rec
        break


@pytest.fixture
def tabix_table_multiline(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz""",
        })
    tabix_to_resource(
        tabix_file(
            """
            #chrom pos_begin c1
            1      1         1
            1      2         2
            1      2         3
            1      3         4
            1      3         5
            1      4         6
            1      4         7
            """, seq_col=0, start_col=1, end_col=1),
        res, "data.bgz"
    )

    table = open_genome_position_table(res, res.config["tabix_table"])
    return table


@pytest.mark.parametrize("pos_beg,pos_end,expected", [
    (1, 1, [("1", "1", "1")]),
    (2, 2, [("1", "2", "2"), ("1", "2", "3")]),
    (3, 3, [("1", "3", "4"), ("1", "3", "5")]),
    (4, 4, [("1", "4", "6"), ("1", "4", "7")]),
    (3, 4, [
        ("1", "3", "4"), ("1", "3", "5"),
        ("1", "4", "6"), ("1", "4", "7")
    ]),
])
def test_tabix_table_multi_get_regions(
        tabix_table_multiline, pos_beg, pos_end, expected):
    table = tabix_table_multiline
    assert table.get_column_names() == ("chrom", "pos_begin", "c1")

    assert not table._should_use_sequential("1", 1)
    for row in table.get_records_in_region("1", 1, 1):
        print(row)

    lines = table.get_records_in_region("1", pos_beg, pos_end)
    lines = list(lines)
    print(lines)
    assert lines == expected


def test_tabix_table_multi_get_regions_partial(tabix_table_multiline):

    table = tabix_table_multiline
    assert table.get_column_names() == ("chrom", "pos_begin", "c1")

    assert not table._should_use_sequential("1", 1)
    for row in table.get_records_in_region("1", 1, 1):
        print(row)

    for index, row in enumerate(table.get_records_in_region("1", 3, 3)):
        print(row)
        if index == 1:
            break

    lines = table.get_records_in_region("1", 3, 3)
    lines = list(lines)
    print(lines)
    assert lines == [("1", "3", "4"), ("1", "3", "5")]


def test_tabix_middle_optimization(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                text_table:
                    filename: data.mem
                tabix_table:
                    filename: data.bgz""",
            "data.mem": """
            """
        })
    tabix_to_resource(
        tabix_file(
            """
            #chrom pos_begin c1
            1      1         1
            1      4         2
            1      4         3
            1      8         4
            1      8         5
            1      12        6
            1      12        7
            """, seq_col=0, start_col=1, end_col=1),
        res, "data.bgz")

    table = open_genome_position_table(res, res.config["tabix_table"])

    row = None
    for row in table.get_records_in_region("1", 1, 1):
        assert row == ("1", "1", "1")
        break
    assert row == ("1", "1", "1")

    row = None
    for row in table.get_records_in_region("1", 1, 1):
        assert row == ("1", "1", "1")
    assert row == ("1", "1", "1")

    row = None
    for row in table.get_records_in_region("1", 2, 2):
        print(row)
    assert row is None


def test_tabix_middle_optimization_regions(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz""",
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom pos_begin pos_end  c1
            1      1         1        1
            1      4         8        2
            1      9         12       3
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz")

    table = open_genome_position_table(res, res.config["tabix_table"])

    row = None
    for row in table.get_records_in_region("1", 1, 1):
        assert row == ("1", "1", "1", "1")
        break

    row = None
    for row in table.get_records_in_region("1", 1, 1):
        assert row == ("1", "1", "1", "1")

    row = None
    for row in table.get_records_in_region("1", 4, 4):
        print(row)
    assert row == ("1", "4", "8", "2")

    row = None
    for row in table.get_records_in_region("1", 4, 4):
        print(row)
        break
    assert row == ("1", "4", "8", "2")

    row = None
    for row in table.get_records_in_region("1", 5, 5):
        print(row)
        break
    assert row == ("1", "4", "8", "2")


def test_tabix_middle_optimization_regions_buggy_1(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz
                    chrom_mapping:
                        add_prefix: chr
            """,
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom pos_begin pos_end  c1
            1      505636    505636   0.006
            1      505637    505637   0.009
            1      505638    505638   0.011
            1      505639    505639   0.013
            1      505640    505641   0.014
            1      505642    505642   0.013
            1      505643    505643   0.012
            1      505644    505645   0.006
            1      505646    505646   0.005
            1      505755    505757   0.004
            1      505758    505758   0.003
            1      505759    505761   0.001
            1      505762    505764   0.002
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz")

    table = open_genome_position_table(res, res.config["tabix_table"])

    rows = None
    rows = list(table.get_records_in_region("chr1", 505637, 505637))
    assert rows == [("chr1", "505637", "505637", "0.009")]

    rows = None
    rows = list(table.get_records_in_region("chr1", 505643, 505646))
    assert rows == [
        ("chr1", "505643", "505643", "0.012"),
        ("chr1", "505644", "505645", "0.006"),
        ("chr1", "505646", "505646", "0.005"),
    ]

    rows = None
    rows = list(table.get_records_in_region("chr1", 505762, 505762))
    assert rows == [
        ("chr1", "505762", "505764", "0.002"),
    ]


def test_buggy_fitcons_e67(tmp_path, tabix_file):

    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz
            """,
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom  pos_begin  pos_end    c1
            5       180739426  180742735  0.065122
            5       180742736  180742736  0.156342
            5       180742737  180742813  0.327393
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz")

    table = open_genome_position_table(res, res.config["tabix_table"])

    rows = None
    rows = list(table.get_records_in_region("5", 180740299, 180740300))
    assert rows == [
        ("5", "180739426", "180742735", "0.065122"),
    ]

    rows = None
    rows = list(table.get_records_in_region("5", 180740301, 180740301))
    assert rows == [
        ("5", "180739426", "180742735", "0.065122"),
    ]


@pytest.mark.parametrize("jump_threshold,expected", [
    ("none", 0),
    ("1", 1),
    ("1500", 1500),
])
def test_tabix_jump_config(tmp_path, tabix_file, jump_threshold, expected):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": f"""
                tabix_table:
                    filename: data.bgz
                    jump_threshold: {jump_threshold}
            """,
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom  pos_begin  pos_end    c1
            5       180739426  180742735  0.065122
            5       180742736  180742736  0.156342
            5       180742737  180742813  0.327393
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz")

    table = open_genome_position_table(res, res.config["tabix_table"])

    assert table.jump_threshold == expected

    rows = None
    rows = list(table.get_records_in_region("5", 180740299, 180740300))
    assert rows == [
        ("5", "180739426", "180742735", "0.065122"),
    ]

    rows = None
    rows = list(table.get_records_in_region("5", 180740301, 180740301))
    assert rows == [
        ("5", "180739426", "180742735", "0.065122"),
    ]


@pytest.mark.parametrize("buffer_maxsize,jump_threshold", [
    (1, 0),
    (2, 1),
    (8, 4),
    (10_000, 2_500),
    (20_000, 2_500),
])
def test_tabix_max_buffer(
        tmp_path, tabix_file, buffer_maxsize, jump_threshold):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": f"""
                tabix_table:
                    filename: data.bgz
                    jump_threshold: {jump_threshold}
            """,
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom  pos_begin  pos_end    c1
            5       180739426  180742735  0.065122
            5       180742736  180742736  0.156342
            5       180742737  180742813  0.327393
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz")

    TabixGenomicPositionTable.BUFFER_MAXSIZE = buffer_maxsize

    table = open_genome_position_table(res, res.config["tabix_table"])
    assert table.BUFFER_MAXSIZE == buffer_maxsize
    assert table.jump_threshold == jump_threshold

    rows = None
    rows = list(table.get_records_in_region("5", 180740299, 180740300))
    assert rows == [
        ("5", "180739426", "180742735", "0.065122"),
    ]

    rows = None
    rows = list(table.get_records_in_region("5", 180740301, 180740301))
    assert rows == [
        ("5", "180739426", "180742735", "0.065122"),
    ]

    rows = None
    rows = list(table.get_records_in_region("5", 180740301, 180742735))
    assert rows == [
        ("5", "180739426", "180742735", "0.065122"),
    ]


def test_contig_length():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem""",
        "data.mem": """
            chrom pos_begin pos2  c2
            1     10        12    3.14
            1     11        11    4.14
            1     12        10    5.14
            1     12        11    6.13
            2     1         2     0"""})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.get_chromosome_length("1") == 13
    assert tab.get_chromosome_length("2") == 2


def test_contig_length_tabix_table(tabix_table):
    assert tabix_table.get_chromosome_length("1") == 13
