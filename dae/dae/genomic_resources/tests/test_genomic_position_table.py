import pytest

from dae.genomic_resources.genome_position_table import \
    TabixGenomicPositionTable, \
    open_genome_position_table

from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo

from dae.genomic_resources.genome_position_table import \
    save_as_tabix_table, LineBuffer
from dae.genomic_resources.test_tools import build_a_test_resource
from dae.genomic_resources.test_tools import convert_to_tab_separated


def test_default_setup():
    res = build_a_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem""",
        "data.mem": """
            chrom pos_begin pos2  c2
            1     10        12    3.14
            1     11        11    4.14
            1     12        10    5.14"""})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 1
    assert tab.pos_end_column_i == 1
    assert tab.get_special_column_index("chrom") == 0
    assert tab.get_special_column_index("pos_begin") == 1
    assert tab.get_special_column_index("pos_end") == 1


def test_regions():
    res = build_a_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem""",
        "data.mem": """
            chrom pos_begin pos_end  c2
            1     10        12       3.14
            1     15        20       4.14
            1     21        30       5.14"""})
    tab = open_genome_position_table(
        res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 1
    assert tab.pos_end_column_i == 2
    assert list(tab.get_all_records()) == [
        ("1",  "10",  "12",  "3.14"),
        ("1",  "15",  "20",  "4.14"),
        ("1",  "21",  "30",  "5.14")
    ]
    assert list(tab.get_records_in_region("1", 11, 11)) == [
        ("1",  "10",  "12",  "3.14")
    ]

    assert list(tab.get_records_in_region("1", 13, 14)) == []

    assert list(tab.get_records_in_region("1", 18, 21)) == [
        ("1",  "15",  "20",  "4.14"),
        ("1",  "21",  "30",  "5.14")
    ]


@pytest.mark.parametrize("jump_threshold", [
    0,
    1,
    2,
    1500,
])
def test_regions_in_tabix(tmp_path, jump_threshold):
    e_gr = build_a_test_resource({
        "genomic_resource.yaml": """
            text_table:
                filename: data.mem
            tabix_table:
                filename: data.bgz""",
        "data.mem": """
            chrom pos_begin pos_end  c2
            1     10        12       3.14
            1     15        20       4.14
            1     21        30       5.14"""})
    txt_tab = open_genome_position_table(
        e_gr, e_gr.config["text_table"])
    d_repo = GenomicResourceDirRepo("b", directory=tmp_path)
    d_repo.store_resource(e_gr)
    d_gr = d_repo.get_resource("")
    save_as_tabix_table(txt_tab,
                        str(d_repo.get_file_path(d_gr, "data.bgz")))
    tab = open_genome_position_table(d_gr, d_gr.config["tabix_table"])
    tab.jump_threshold = jump_threshold

    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 1
    assert tab.pos_end_column_i == 2
    assert list(tab.get_all_records()) == [
        ("1",  "10",  "12",  "3.14"),
        ("1",  "15",  "20",  "4.14"),
        ("1",  "21",  "30",  "5.14")
    ]
    assert list(tab.get_records_in_region("1", 11, 11)) == [
        ("1",  "10",  "12",  "3.14")
    ]

    assert list(tab.get_records_in_region("1", 13, 14)) == []

    assert list(tab.get_records_in_region("1", 18, 21)) == [
        ("1",  "15",  "20",  "4.14"),
        ("1",  "21",  "30",  "5.14")
    ]


def test_chr_add_pref():
    res = build_a_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                chrom_mapping:
                    add_prefix: chr""",
        "data.mem": """
            chrom pos_begin pos2  c2
            1     10        12    3.14
            X     11        11    4.14
            11    12        10    5.14"""})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.get_chromosomes() == ["chr1", "chr11", "chrX"]


def test_chr_del_pref():
    res = build_a_test_resource({
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
    res = build_a_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                chrom_mapping:
                    filename: chrom_map.txt""",
        "data.mem": """
            chrom    pos_begin pos2  c2
            chr1     10        12    3.14
            chr22    11        11    4.14
            chrX     12        10    5.14""",
        "chrom_map.txt": convert_to_tab_separated("""
            chrom   file_chrom
            gosho   chr1
            pesho   chr22
        """)})
    tab = open_genome_position_table(
        res, res.config["table"])

    assert tab.get_chromosomes() == ["gosho", "pesho"]
    assert list(tab.get_all_records()) == [
        ("gosho",  "10",  "12",  "3.14"),
        ("pesho",  "11",  "11",  "4.14")
    ]
    assert list(tab.get_records_in_region("pesho")) == [
        ("pesho",  "11",  "11",  "4.14"),
    ]


def test_chrom_mapping_file_with_tabix(tmp_path):
    e_gr = build_a_test_resource({
        "genomic_resource.yaml": """
            text_table:
                filename: data.mem
            tabix_table:
                filename: data.bgz
                chrom_mapping:
                    filename: chrom_map.txt""",
        "data.mem": """
            chrom    pos_begin pos2  c2
            chr1     10        12    3.14
            chr22    11        11    4.14
            chrX     12        10    5.14""",
        "chrom_map.txt": convert_to_tab_separated("""
                chrom   file_chrom
                gosho   chr1
                pesho   chr22
        """)})
    d_repo = GenomicResourceDirRepo("b", directory=tmp_path)
    d_repo.store_resource(e_gr)
    d_gr = d_repo.get_resource("")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config["text_table"]),
        str(d_repo.get_file_path(d_gr, "data.bgz")))
    tab = open_genome_position_table(d_gr, d_gr.config["tabix_table"])

    assert tab.get_chromosomes() == ["gosho", "pesho"]
    assert list(tab.get_all_records()) == [
        ("gosho",  "10",  "12",  "3.14"),
        ("pesho",  "11",  "11",  "4.14")
    ]
    assert list(tab.get_records_in_region("pesho")) == [
        ("pesho",  "11",  "11",  "4.14"),
    ]


def test_column_with_name():
    res = build_a_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                pos_begin:
                    name: pos2""",
        "data.mem": """
            chrom pos pos2 c2
            1     10  12   3.14
            1     11  11   4.14
            1     12  10   5.14"""})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region("1", 12, 12)) == [
        ("1", "10", "12", "3.14")]


def test_column_with_index():
    res = build_a_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                pos_begin:
                    index: 2""",
        "data.mem": """
            chrom pos pos2  c2
            1     10  12    3.14
            1     11  11    4.14
            1     12  10    5.14"""})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region("1", 12, 12)) == [
        ("1", "10", "12", "3.14")]


# def test_non_default_keys():
#     res = build_a_test_resource({
#         "genomic_resource.yaml": """
#             table:
#                 filename: data.mem
#                 chrom.name: chr
#                 pos_start.index: 2""",
#         "data.mem": """
#             chr pos pos2  c2
#             1   10  12  3.14
#             1   11  11  4.14
#             1   12  10  5.14"""})
#     tab = open_genome_position_table(
#         res, res.config["table"], "chrom", "pos_start")
#     assert tab.chrom_column_i == 0
#     assert tab.pos_begin_column_i == 2
#     assert list(tab.get_records_in_region("1", 12, 12)) == [
#         ("1", "10", "12", "3.14")]


def test_no_header():
    res = build_a_test_resource({
        "genomic_resource.yaml": """
            table:
                header_mode: none
                filename: data.mem
                chrom:
                    index: 0
                pos_begin:
                    index: 2""",
        "data.mem": """
            1   10  12  3.14
            1   11  11  4.14
            1   12  10  5.14"""})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region("1", 12, 12)) == [
        ("1", "10", "12", "3.14")]


def test_header_in_config():
    res = build_a_test_resource({
        "genomic_resource.yaml": """
            table:
                header_mode: list
                header: ["chrom", "pos", "pos2", "score"]
                filename: data.mem
                pos_begin:
                    name: pos2""",
        "data.mem": """
            1   10  12  3.14
            1   11  11  4.14
            1   12  10  5.14"""})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region("1", 12, 12)) == [
        ("1", "10", "12", "3.14")]


def test_space_in_mem_table():
    res = build_a_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem""",
        "data.mem": """
            chrom pos_begin pos2   c2
            1     10        12     3.14
            1     11        EMPTY  4.14
            1     12        10     5.14"""})
    tab = open_genome_position_table(res, res.config["table"])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 1
    assert list(tab.get_records_in_region("1", 11, 11)) == [
        ("1", "11", "", "4.14")]


def test_text_table():
    repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": """
                    table:
                        filename: data.mem""",
                "data.mem": """
                    chrom pos_begin c1     c2
                    1     3         3.14   aa
                    1     4         4.14   bb
                    1     4         5.14   cc
                    1     5         6.14   dd
                    1     8         7.14   ee
                    2     3         8.14   ff"""
            }
        }
        })
    gr = repo.get_resource("one")
    table = open_genome_position_table(gr, gr.config["table"])
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

    assert list(table.get_records_in_region("1", 20, 25)) == []

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
def test_tabix_table(tmp_path, jump_threshold):
    e_repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": """
                    text_table:
                        filename: data.mem
                    tabix_table:
                        filename: data.bgz""",
                "data.mem": """
                    chrom pos_begin c1     c2
                    1     3         3.14   aa
                    1     4         4.14   bb
                    1     4         5.14   cc
                    1     5         6.14   dd
                    1     8         7.14   ee
                    2     3         8.14   ff"""
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config["text_table"]),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = open_genome_position_table(d_gr, d_gr.config["tabix_table"])
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

    assert list(table.get_records_in_region("1", 20, 25)) == []

    assert list(table.get_records_in_region("2", None, None)) == [
        ("2", "3", "8.14", "ff")
    ]

    with pytest.raises(Exception):
        list(table.get_records_in_region("3"))


@pytest.fixture
def tabix_table(tmp_path):
    e_repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": """
                    text_table:
                        filename: data.mem
                    tabix_table:
                        filename: data.bgz""",
                "data.mem": """
                    chrom pos_begin c1
                    1     1         1
                    1     2         2
                    1     3         3
                    1     4         4
                    1     5         5
                    1     6         6
                    1     7         7
                    1     8         8
                    1     9         9
                    1     10        10
                    1     11        11
                    1     12        12
                """
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config["text_table"]),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = open_genome_position_table(d_gr, d_gr.config["tabix_table"])
    return table


@pytest.fixture
def regions_tabix_table(tmp_path):
    e_repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": """
                    text_table:
                        filename: data.mem
                    tabix_table:
                        filename: data.bgz""",
                "data.mem": """
                    chrom pos_begin pos_end  c1
                    1     1         5        1
                    1     6         10       2
                    1     11        15       3
                    1     16        20       4
                    1     21        25       5
                    1     26        30       6
                """
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config["text_table"]),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = open_genome_position_table(d_gr, d_gr.config["tabix_table"])
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


# @pytest.mark.parametrize("pos_beg,pos_end,expected", [
#     (0, 1, None),
#     (1, 2, None),
#     (5, 6, [("1", "6", "10", "2")]),
#     (9, 15, [("1", "6", "10", "2")]),
#     (7, 20, [("1", "6", "10", "2")]),
#     (11, 12, [("1", "11", "15", "3")]),
# ])
# def test_regions_tabix_table_sequential_rewind(
#         regions_tabix_table, pos_beg, pos_end, expected):
#     table = regions_tabix_table
#     assert table.get_column_names() == ("chrom", "pos_begin", "pos_end", "c1")

#     assert not table._should_use_sequential("1", 1)
#     for row in table.get_records_in_region("1", 2, 2):
#         print(row)
#     assert table.current_pos()[1] == 6
#     assert table.current_pos()[2] == 10

#     # buff = table._sequential_rewind("1", pos_beg, pos_end)
#     # if buff: 
#     #     buff = [tuple(line) for line in buff]
#     # assert buff == expected


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

    lines = list(table.get_records_in_region("1", 1, 1))
    print(lines)
    lines = list(table.get_records_in_region("1", 1, 1))
    print(lines)



@pytest.fixture
def tabix_table_multiline(tmp_path):
    e_repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": """
                    text_table:
                        filename: data.mem
                    tabix_table:
                        filename: data.bgz""",
                "data.mem": """
                    chrom pos_begin c1
                    1     1         1
                    1     2         2
                    1     2         3
                    1     3         4
                    1     3         5
                    1     4         6
                    1     4         7
                """
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config["text_table"]),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = open_genome_position_table(d_gr, d_gr.config["tabix_table"])
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


def test_tabix_middle_optimization(tmp_path):
    e_repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": """
                    text_table:
                        filename: data.mem
                    tabix_table:
                        filename: data.bgz""",
                "data.mem": """
                    chrom pos_begin c1
                    1     1         1
                    1     4         2
                    1     4         3
                    1     8         4
                    1     8         5
                    1     12        6
                    1     12        7
                """
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config["text_table"]),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = open_genome_position_table(d_gr, d_gr.config["tabix_table"])

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


def test_tabix_middle_optimization_regions(tmp_path):
    e_repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": """
                    text_table:
                        filename: data.mem
                    tabix_table:
                        filename: data.bgz""",
                "data.mem": """
                    chrom pos_begin pos_end  c1
                    1     1         1        1
                    1     4         8        2
                    1     9         12       3
                """
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config["text_table"]),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = open_genome_position_table(d_gr, d_gr.config["tabix_table"])

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


def test_tabix_middle_optimization_regions_buggy_1(tmp_path):
    e_repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": """
                    text_table:
                        filename: data.mem
                    tabix_table:
                        filename: data.bgz
                        chrom_mapping:
                            add_prefix: chr
                """,
                "data.mem": """
                    chrom pos_begin pos_end  c1
                    1     505636    505636   0.006
                    1     505637    505637   0.009
                    1     505638    505638   0.011
                    1     505639    505639   0.013
                    1     505640    505641   0.014
                    1     505642    505642   0.013
                    1     505643    505643   0.012
                    1     505644    505645   0.006
                    1     505646    505646   0.005
                    1     505755    505757   0.004
                    1     505758    505758   0.003
                    1     505759    505761   0.001
                    1     505762    505764   0.002                """
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config["text_table"]),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = open_genome_position_table(d_gr, d_gr.config["tabix_table"])

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


def test_buggy_fitcons_e67(tmp_path):

    e_repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": """
                    text_table:
                        filename: data.mem
                    tabix_table:
                        filename: data.bgz
                """,
                "data.mem": """
                    chrom  pos_begin  pos_end    c1
                    5      180739426  180742735  0.065122
                    5      180742736  180742736  0.156342
                    5      180742737  180742813  0.327393    
                """
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config["text_table"]),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = open_genome_position_table(d_gr, d_gr.config["tabix_table"])

    rows = None
    rows = list(table.get_records_in_region('5', 180740299, 180740300))
    assert rows == [
        ('5', '180739426', '180742735', '0.065122'),
    ]

    rows = None
    rows = list(table.get_records_in_region('5', 180740301, 180740301))
    assert rows == [
        ('5', '180739426', '180742735', '0.065122'),
    ]


@pytest.mark.parametrize("jump_threshold,expected", [
    ("none", 0),
    ("1", 1),
    ("1500", 1500),
])
def test_tabix_jump_config(tmp_path, jump_threshold, expected):
    e_repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": f"""
                    text_table:
                        filename: data.mem
                    tabix_table:
                        filename: data.bgz
                        jump_threshold: {jump_threshold}
                """,
                "data.mem": """
                    chrom  pos_begin  pos_end    c1
                    5      180739426  180742735  0.065122
                    5      180742736  180742736  0.156342
                    5      180742737  180742813  0.327393    
                """
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config["text_table"]),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = open_genome_position_table(d_gr, d_gr.config["tabix_table"])
    assert table.jump_threshold == expected

    rows = None
    rows = list(table.get_records_in_region('5', 180740299, 180740300))
    assert rows == [
        ('5', '180739426', '180742735', '0.065122'),
    ]

    rows = None
    rows = list(table.get_records_in_region('5', 180740301, 180740301))
    assert rows == [
        ('5', '180739426', '180742735', '0.065122'),
    ]


@pytest.mark.parametrize("buffer_maxsize,jump_threshold", [
    (1, 0),
    (2, 1),
    (8, 4),
    (10_000, 2_500),
    (20_000, 2_500),
])
def test_tabix_max_buffer(tmp_path, buffer_maxsize, jump_threshold):
    e_repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": """
                    text_table:
                        filename: data.mem
                    tabix_table:
                        filename: data.bgz
                """,
                "data.mem": """
                    chrom  pos_begin  pos_end    c1
                    5      180739426  180742735  0.065122
                    5      180742736  180742736  0.156342
                    5      180742737  180742813  0.327393    
                """
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config["text_table"]),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    TabixGenomicPositionTable.BUFFER_MAXSIZE = buffer_maxsize

    table = open_genome_position_table(d_gr, d_gr.config["tabix_table"])
    assert table.BUFFER_MAXSIZE == buffer_maxsize
    assert table.jump_threshold == jump_threshold

    rows = None
    rows = list(table.get_records_in_region('5', 180740299, 180740300))
    assert rows == [
        ('5', '180739426', '180742735', '0.065122'),
    ]

    rows = None
    rows = list(table.get_records_in_region('5', 180740301, 180740301))
    assert rows == [
        ('5', '180739426', '180742735', '0.065122'),
    ]

    rows = None
    rows = list(table.get_records_in_region('5', 180740301, 180742735))
    assert rows == [
        ('5', '180739426', '180742735', '0.065122'),
    ]
