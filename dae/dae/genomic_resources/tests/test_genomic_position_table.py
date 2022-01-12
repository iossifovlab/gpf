import pytest

from dae.genomic_resources.genome_position_table import \
    open_genome_position_table

from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo

from dae.genomic_resources.genome_position_table import \
    save_as_tabix_table
from dae.genomic_resources.test_tools import build_a_test_resource
from dae.genomic_resources.test_tools import convert_to_tab_separated


def test_default_setup():
    res = build_a_test_resource({
        "genomic_resource.yaml": '''
            table:
                filename: data.mem''',
        "data.mem": '''
            chrom pos_begin pos2  c2
            1     10        12    3.14
            1     11        11    4.14
            1     12        10    5.14'''})
    tab = open_genome_position_table(res, res.config['table'])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 1
    assert tab.pos_end_column_i == 1
    assert tab.get_special_column_index("chrom") == 0
    assert tab.get_special_column_index("pos_begin") == 1
    assert tab.get_special_column_index("pos_end") == 1


def test_regions():
    res = build_a_test_resource({
        "genomic_resource.yaml": '''
            table:
                filename: data.mem''',
        "data.mem": '''
            chrom pos_begin pos_end  c2
            1     10        12       3.14
            1     15        20       4.14
            1     21        30       5.14'''})
    tab = open_genome_position_table(
        res, res.config['table'])
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


def test_regions_in_tabix(tmp_path):
    e_gr = build_a_test_resource({
        "genomic_resource.yaml": '''
            text_table:
                filename: data.mem
            tabix_table:
                filename: data.bgz''',
        "data.mem": '''
            chrom pos_begin pos_end  c2
            1     10        12       3.14
            1     15        20       4.14
            1     21        30       5.14'''})
    txt_tab = open_genome_position_table(
        e_gr, e_gr.config['text_table'])
    d_repo = GenomicResourceDirRepo("b", directory=tmp_path)
    d_repo.store_resource(e_gr)
    d_gr = d_repo.get_resource("")
    save_as_tabix_table(txt_tab,
                        str(d_repo.get_file_path(d_gr, "data.bgz")))
    tab = open_genome_position_table(d_gr, d_gr.config['tabix_table'])

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
        "genomic_resource.yaml": '''
            table:
                filename: data.mem
                chrom_mapping:
                    add_prefix: chr''',
        "data.mem": '''
            chrom pos_begin pos2  c2
            1     10        12    3.14
            X     11        11    4.14
            11    12        10    5.14'''})
    tab = open_genome_position_table(res, res.config['table'])
    assert tab.get_chromosomes() == ["chr1", "chr11", "chrX"]


def test_chr_del_pref():
    res = build_a_test_resource({
        "genomic_resource.yaml": '''
            table:
                filename: data.mem
                chrom_mapping:
                    del_prefix: chr''',
        "data.mem": '''
            chrom    pos_begin pos2  c2
            chr1     10        12    3.14
            chr22    11        11    4.14
            chrX     12        10    5.14'''})
    tab = open_genome_position_table(res, res.config['table'])
    assert tab.get_chromosomes() == ["1", "22", "X"]


def test_chrom_mapping_file():
    res = build_a_test_resource({
        "genomic_resource.yaml": '''
            table:
                filename: data.mem
                chrom_mapping:
                    filename: chrom_map.txt''',
        "data.mem": '''
            chrom    pos_begin pos2  c2
            chr1     10        12    3.14
            chr22    11        11    4.14
            chrX     12        10    5.14''',
        "chrom_map.txt": convert_to_tab_separated('''
            chrom   file_chrom
            gosho   chr1
            pesho   chr22
        ''')})
    tab = open_genome_position_table(
        res, res.config['table'])

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
        "genomic_resource.yaml": '''
            text_table:
                filename: data.mem
            tabix_table:
                filename: data.bgz
                chrom_mapping:
                    filename: chrom_map.txt''',
        "data.mem": '''
            chrom    pos_begin pos2  c2
            chr1     10        12    3.14
            chr22    11        11    4.14
            chrX     12        10    5.14''',
        "chrom_map.txt": convert_to_tab_separated('''
                chrom   file_chrom
                gosho   chr1
                pesho   chr22
        ''')})
    d_repo = GenomicResourceDirRepo("b", directory=tmp_path)
    d_repo.store_resource(e_gr)
    d_gr = d_repo.get_resource("")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config['text_table']),
        str(d_repo.get_file_path(d_gr, "data.bgz")))
    tab = open_genome_position_table(d_gr, d_gr.config['tabix_table'])

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
        "genomic_resource.yaml": '''
            table:
                filename: data.mem
                pos_begin:
                    name: pos2''',
        "data.mem": '''
            chrom pos pos2 c2
            1     10  12   3.14
            1     11  11   4.14
            1     12  10   5.14'''})
    tab = open_genome_position_table(res, res.config['table'])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region('1', 12, 12)) == [
        ('1', '10', '12', '3.14')]


def test_column_with_index():
    res = build_a_test_resource({
        "genomic_resource.yaml": '''
            table:
                filename: data.mem
                pos_begin:
                    index: 2''',
        "data.mem": '''
            chrom pos pos2  c2
            1     10  12    3.14
            1     11  11    4.14
            1     12  10    5.14'''})
    tab = open_genome_position_table(res, res.config['table'])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region('1', 12, 12)) == [
        ('1', '10', '12', '3.14')]


# def test_non_default_keys():
#     res = build_a_test_resource({
#         "genomic_resource.yaml": '''
#             table:
#                 filename: data.mem
#                 chrom.name: chr
#                 pos_start.index: 2''',
#         "data.mem": '''
#             chr pos pos2  c2
#             1   10  12  3.14
#             1   11  11  4.14
#             1   12  10  5.14'''})
#     tab = open_genome_position_table(
#         res, res.config['table'], "chrom", "pos_start")
#     assert tab.chrom_column_i == 0
#     assert tab.pos_begin_column_i == 2
#     assert list(tab.get_records_in_region('1', 12, 12)) == [
#         ('1', '10', '12', '3.14')]


def test_no_header():
    res = build_a_test_resource({
        "genomic_resource.yaml": '''
            table:
                header_mode: none
                filename: data.mem
                chrom:
                    index: 0
                pos_begin:
                    index: 2''',
        "data.mem": '''
            1   10  12  3.14
            1   11  11  4.14
            1   12  10  5.14'''})
    tab = open_genome_position_table(res, res.config['table'])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region('1', 12, 12)) == [
        ('1', '10', '12', '3.14')]


def test_header_in_config():
    res = build_a_test_resource({
        "genomic_resource.yaml": '''
            table:
                header_mode: list
                header: ["chrom", "pos", "pos2", "score"]
                filename: data.mem
                pos_begin:
                    name: pos2''',
        "data.mem": '''
            1   10  12  3.14
            1   11  11  4.14
            1   12  10  5.14'''})
    tab = open_genome_position_table(res, res.config['table'])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 2
    assert list(tab.get_records_in_region('1', 12, 12)) == [
        ('1', '10', '12', '3.14')]


def test_space_in_mem_table():
    res = build_a_test_resource({
        "genomic_resource.yaml": '''
            table:
                filename: data.mem''',
        "data.mem": '''
            chrom pos_begin pos2   c2
            1     10        12     3.14
            1     11        EMPTY  4.14
            1     12        10     5.14'''})
    tab = open_genome_position_table(res, res.config['table'])
    assert tab.chrom_column_i == 0
    assert tab.pos_begin_column_i == 1
    assert list(tab.get_records_in_region('1', 11, 11)) == [
        ('1', '11', '', '4.14')]


def test_text_table():
    repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": '''
                    table:
                        filename: data.mem''',
                "data.mem": '''
                    chrom pos_begin c1     c2
                    1     3         3.14   aa
                    1     4         4.14   bb
                    1     4         5.14   cc
                    1     5         6.14   dd
                    1     8         7.14   ee
                    2     3         8.14   ff'''
            }
        }
        })
    gr = repo.get_resource("one")
    table = open_genome_position_table(gr, gr.config['table'])
    assert table.get_column_names() == ('chrom', 'pos_begin', 'c1', 'c2')

    assert list(table.get_all_records()) == [
        ('1', '3', '3.14', 'aa'),
        ('1', '4', '4.14', 'bb'),
        ('1', '4', '5.14', 'cc'),
        ('1', '5', '6.14', 'dd'),
        ('1', '8', '7.14', 'ee'),
        ('2', '3', '8.14', 'ff')
    ]

    assert list(table.get_records_in_region("1", 4, 5)) == [
        ('1', '4', '4.14', 'bb'),
        ('1', '4', '5.14', 'cc'),
        ('1', '5', '6.14', 'dd')
    ]

    assert list(table.get_records_in_region("1", 4, None)) == [
        ('1', '4', '4.14', 'bb'),
        ('1', '4', '5.14', 'cc'),
        ('1', '5', '6.14', 'dd'),
        ('1', '8', '7.14', 'ee')
    ]

    assert list(table.get_records_in_region("1", None, 4)) == [
        ('1', '3', '3.14', 'aa'),
        ('1', '4', '4.14', 'bb'),
        ('1', '4', '5.14', 'cc')
    ]

    assert list(table.get_records_in_region("1", 20, 25)) == []

    assert list(table.get_records_in_region("2", None, None)) == [
        ('2', '3', '8.14', 'ff')
    ]

    with pytest.raises(Exception):
        list(table.get_records_in_region('3'))


def test_tabix_table(tmp_path):
    e_repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": '''
                    text_table:
                        filename: data.mem
                    tabix_table:
                        filename: data.bgz''',
                "data.mem": '''
                    chrom pos_begin c1     c2
                    1     3         3.14   aa
                    1     4         4.14   bb
                    1     4         5.14   cc
                    1     5         6.14   dd
                    1     8         7.14   ee
                    2     3         8.14   ff'''
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        open_genome_position_table(e_gr, e_gr.config['text_table']),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = open_genome_position_table(d_gr, d_gr.config['tabix_table'])
    assert table.get_column_names() == ('chrom', 'pos_begin', 'c1', 'c2')

    assert list(table.get_all_records()) == [
        ('1', '3', '3.14', 'aa'),
        ('1', '4', '4.14', 'bb'),
        ('1', '4', '5.14', 'cc'),
        ('1', '5', '6.14', 'dd'),
        ('1', '8', '7.14', 'ee'),
        ('2', '3', '8.14', 'ff')
    ]

    assert list(table.get_records_in_region("1", 4, 5)) == [
        ('1', '4', '4.14', 'bb'),
        ('1', '4', '5.14', 'cc'),
        ('1', '5', '6.14', 'dd')
    ]

    assert list(table.get_records_in_region("1", 4, None)) == [
        ('1', '4', '4.14', 'bb'),
        ('1', '4', '5.14', 'cc'),
        ('1', '5', '6.14', 'dd'),
        ('1', '8', '7.14', 'ee')
    ]

    assert list(table.get_records_in_region("1", None, 4)) == [
        ('1', '3', '3.14', 'aa'),
        ('1', '4', '4.14', 'bb'),
        ('1', '4', '5.14', 'cc')
    ]

    assert list(table.get_records_in_region("1", 20, 25)) == []

    assert list(table.get_records_in_region("2", None, None)) == [
        ('2', '3', '8.14', 'ff')
    ]

    with pytest.raises(Exception):
        list(table.get_records_in_region('3'))
