# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines

import textwrap
import pytest
# pylint: disable=no-member
import pysam

from dae.genomic_resources.genomic_position_table import \
    TabixGenomicPositionTable, \
    VCFGenomicPositionTable, \
    build_genomic_position_table
from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol

from dae.genomic_resources.testing import \
    build_test_resource, \
    tabix_to_resource
from dae.testing import convert_to_tab_separated, setup_directories, setup_vcf


@pytest.fixture
def vcf_res(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("vcf")
    setup_directories(
        root_path / "grr",
        {
            "tmp": {
                "genomic_resource.yaml": textwrap.dedent("""
                    tabix_table:
                        filename: data.vcf.gz
                        format: vcf_info
                """)
            }
        }
    )
    setup_vcf(
        root_path / "grr" / "tmp" / "data.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.1
##INFO=<ID=A,Number=1,Type=Integer,Description="Score A">
##INFO=<ID=B,Number=1,Type=Integer,Description="Score B">
##INFO=<ID=C,Number=.,Type=String,Description="Score C">
##INFO=<ID=D,Number=.,Type=String,Description="Score D">
#CHROM POS ID REF ALT QUAL FILTER  INFO
chr1   5   .  A   T   .    .       A=1;C=c11,c12;D=d11
chr1   15   .  A   T   .    .       A=2;B=21;C=c21;D=d21,d22
chr1   30   .  A   T   .    .       A=3;B=31;C=c21;D=d31,d32
    """)
    )
    proto = build_fsspec_protocol("testing", str(root_path / "grr"))
    return proto.get_resource("tmp")


@pytest.fixture
def vcf_res_autodetect_format(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("vcf")
    setup_directories(
        root_path / "grr",
        {
            "tmp": {
                "genomic_resource.yaml": textwrap.dedent("""
                    tabix_table:
                        filename: data.vcf.gz
                """)
            }
        }
    )
    setup_vcf(
        root_path / "grr" / "tmp" / "data.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.1
##INFO=<ID=A,Number=1,Type=Integer,Description="Score A">
#CHROM POS ID REF ALT QUAL FILTER  INFO
chr1   5   .  A   T   .    .       A=1
    """)
    )
    proto = build_fsspec_protocol("testing", str(root_path / "grr"))
    return proto.get_resource("tmp")


@pytest.fixture
def vcf_res_score_conf_override(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("vcf")
    setup_directories(
        root_path / "grr",
        {
            "tmp": {
                "genomic_resource.yaml": textwrap.dedent("""
                    tabix_table:
                        filename: data.vcf.gz
                        scores:
                        - id: A
                          name: A
                          type: float
                          desc: Score A, but overriden
                """)
            }
        }
    )
    setup_vcf(
        root_path / "grr" / "tmp" / "data.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.1
##INFO=<ID=A,Number=1,Type=Integer,Description="Score A">
#CHROM POS ID REF ALT QUAL FILTER  INFO
chr1   5   .  A   T   .    .       A=1
    """)
    )
    proto = build_fsspec_protocol("testing", str(root_path / "grr"))
    return proto.get_resource("tmp")



@pytest.fixture
def vcf_res_multiallelic(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("vcf")
    setup_directories(
        root_path / "grr",
        {
            "tmp": {
                "genomic_resource.yaml": textwrap.dedent("""
                    tabix_table:
                        filename: data.vcf.gz
                        format: vcf_info
                """)
            }
        }
    )
    setup_vcf(
        root_path / "grr" / "tmp" / "data.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.1
##INFO=<ID=A,Number=1,Type=Integer,Description="Score A">
##INFO=<ID=B,Number=.,Type=Integer,Description="Score B">
##INFO=<ID=C,Number=R,Type=String,Description="Score C">
##INFO=<ID=D,Number=A,Type=String,Description="Score D">
#CHROM POS ID REF ALT QUAL FILTER  INFO
chr1   2   .  A   .   .    .       A=0;B=01,02,03;C=c01
chr1   5   .  A   T   .    .       A=1;B=11,12,13;C=c11,c12;D=d11
chr1   15   .  A   T,G   .    .       A=2;B=21,22;C=c21,c22,c23;D=d21,d22
chr1   30   .  A   T,G,C   .    .       A=3;B=31;C=c31,c32,c33,c34;D=d31,d32,d33
    """)
    )
    proto = build_fsspec_protocol("testing", str(root_path / "grr"))
    return proto.get_resource("tmp")


def test_default_setup():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                scores:
                - id: c2
                  name: c2
                  type: float""",
        "data.mem": convert_to_tab_separated("""
            chrom pos_begin pos2  c2
            1     10        12    3.14
            1     11        11    4.14
            1     12        10    5.14""")})
    with build_genomic_position_table(res, res.config["table"]) as tab:
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
                filename: data.mem
                scores:
                - id: c2
                  name: c2
                  type: float""",
        "data.mem": convert_to_tab_separated("""
            chrom pos_begin pos_end  c2
            1     10        12       3.14
            1     15        20       4.14
            1     21        30       5.14""")})

    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert tab.chrom_column_i == 0
        assert tab.pos_begin_column_i == 1
        assert tab.pos_end_column_i == 2
        assert list(tab.get_all_records()) == [
            ("1", 10, 12, "3.14"),
            ("1", 15, 20, "4.14"),
            ("1", 21, 30, "5.14")
        ]

        assert list(tab.get_records_in_region("1", 11, 11)) == [
            ("1", 10, 12, "3.14")
        ]

        assert not list(tab.get_records_in_region("1", 13, 14))

        assert list(tab.get_records_in_region("1", 18, 21)) == [
            ("1", 15, 20, "4.14"),
            ("1", 21, 30, "5.14")
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
                    filename: data.bgz
                    scores:
                    - id: c2
                      name: c2
                      type: float""",
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

    with build_genomic_position_table(res, res.config["tabix_table"]) as tab:
        assert tab
        tab.jump_threshold = jump_threshold
        assert tab.chrom_column_i == 0
        assert tab.pos_begin_column_i == 1
        assert tab.pos_end_column_i == 2
        assert list(tab.get_all_records()) == [
            ("1", 10, 12, "3.14"),
            ("1", 15, 20, "4.14"),
            ("1", 21, 30, "5.14")
        ]
        assert list(tab.get_records_in_region("1", 11, 11)) == [
            ("1", 10, 12, "3.14")
        ]
        assert not list(tab.get_records_in_region("1", 13, 14))
        assert list(tab.get_records_in_region("1", 18, 21)) == [
            ("1", 15, 20, "4.14"),
            ("1", 21, 30, "5.14")
        ]


def test_last_call_is_updated(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz
                    scores:
                    - id: c2
                      name: c2
                      type: float""",
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

    with build_genomic_position_table(res, res.config["tabix_table"]) as tab:
        assert tab._last_call == ("", -1, -1)
        assert list(tab.get_records_in_region("1", 11, 11)) == [
            ("1", 10, 12, "3.14")
        ]
        assert tab._last_call == ("1", 11, 11)
        assert not list(tab.get_records_in_region("1", 13, 14))
        assert tab._last_call == ("1", 13, 14)
        assert list(tab.get_records_in_region("1", 18, 21)) == [
            ("1", 15, 20, "4.14"),
            ("1", 21, 30, "5.14")
        ]
        assert tab._last_call == ("1", 18, 21)


def test_chr_add_pref():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                chrom_mapping:
                    add_prefix: chr
                scores:
                - id: c2
                  name: c2
                  type: float""",
        "data.mem": convert_to_tab_separated(
            """
            chrom pos_begin pos2  c2
            1     10        12    3.14
            X     11        11    4.14
            11    12        10    5.14
            """)})
    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert tab.get_chromosomes() == ["chr1", "chr11", "chrX"]


def test_chr_del_pref():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                chrom_mapping:
                    del_prefix: chr
                scores:
                - id: c2
                  name: c2
                  type: float""",
        "data.mem": """
            chrom    pos_begin pos2  c2
            chr1     10        12    3.14
            chr22    11        11    4.14
            chrX     12        10    5.14"""})
    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert tab.get_chromosomes() == ["1", "22", "X"]


def test_chrom_mapping_file():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                chrom_mapping:
                    filename: chrom_map.txt
                pos_end:
                    name: pos2
                scores:
                - id: c2
                  name: c2
                  type: float""",
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
    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert tab.get_chromosomes() == ["gosho", "pesho"]
        assert list(tab.get_all_records()) == [
            ("gosho", 10, 12, "3.14"),
            ("pesho", 11, 11, "4.14")
        ]
        assert list(tab.get_records_in_region("pesho")) == [
            ("pesho", 11, 11, "4.14"),
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
                        filename: chrom_map.txt
                    pos_end:
                        name: pos2
                    scores:
                    - id: c2
                      name: c2
                      type: float""",
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
    with build_genomic_position_table(res, res.config["tabix_table"]) as tab:
        assert tab.get_chromosomes() == ["gosho", "pesho"]
        assert list(tab.get_all_records()) == [
            ("gosho", 10, 12, "3.14"),
            ("pesho", 11, 11, "4.14")
        ]
        assert list(tab.get_records_in_region("pesho")) == [
            ("pesho", 11, 11, "4.14"),
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
        build_genomic_position_table(res, res.config["tabix_table"]).open()

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
                    name: pos2
                scores:
                - id: c2
                  name: c2
                  type: float""",
        "data.mem": convert_to_tab_separated(
            """
            chrom pos pos2 c2
            1     10  12   3.14
            1     11  11   4.14
            1     12  14   5.14
            """)
    })
    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert tab.chrom_column_i == 0
        assert tab.pos_begin_column_i == 2
        assert list(tab.get_records_in_region("1", 12, 12)) == [
            ("1", 12, 12, "10", "3.14")]


def test_column_with_index():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                pos_begin:
                    index: 2
                scores:
                - id: c2
                  name: c2
                  type: float""",
        "data.mem": convert_to_tab_separated("""
            chrom pos pos2  c2
            1     10  12    3.14
            1     11  11    4.14
            1     12  14    5.14""")
    })
    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert tab.chrom_column_i == 0
        assert tab.pos_begin_column_i == 2
        assert list(tab.get_records_in_region("1", 12, 12)) == [
            ("1", 12, 12, "10", "3.14")]


def test_no_header():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                header_mode: none
                filename: data.mem
                chrom:
                    index: 0
                pos_begin:
                    index: 2
                scores:
                - id: c2
                  name: c2
                  type: float""",
        "data.mem": convert_to_tab_separated("""
            1   10  12  3.14
            1   11  11  4.14
            1   12  14  5.14
            """)
    })
    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert tab.chrom_column_i == 0
        assert tab.pos_begin_column_i == 2
        assert list(tab.get_records_in_region("1", 12, 12)) == [
            ("1", 12, 12, "10", "3.14")]


def test_header_in_config():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                header_mode: list
                header: ["chrom", "pos", "pos2", "score"]
                filename: data.mem
                pos_begin:
                    name: pos2
                scores:
                - id: c2
                  name: c2
                  type: float""",
        "data.mem": convert_to_tab_separated("""
            1   10  12  3.14
            1   11  11  4.14
            1   12  10  5.14""")})
    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert tab.chrom_column_i == 0
        assert tab.pos_begin_column_i == 2
        assert list(tab.get_records_in_region("1", 12, 12)) == [
            ("1", 12, 12, "10", "3.14")]


def test_space_in_mem_table():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                scores:
                - id: c2
                  name: c2
                  type: float""",
        "data.mem": convert_to_tab_separated("""
            chrom pos_begin pos2   c2
            1     10        12     3.14
            1     11        EMPTY  4.14
            1     12        10     5.14""")})
    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert tab.chrom_column_i == 0
        assert tab.pos_begin_column_i == 1
        assert list(tab.get_records_in_region("1", 11, 11)) == [
            ("1", 11, 11, "", "4.14")]


def test_text_table():
    res = build_test_resource(
        content={
            "genomic_resource.yaml": """
                table:
                    filename: data.mem
                    scores:
                    - id: c2
                      name: c2
                      type: float""",
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

    with build_genomic_position_table(res, res.config["table"]) as table:
        assert table.get_column_names() == ("chrom", "pos_begin", "c1", "c2")
        assert list(table.get_all_records()) == [
            ("1", 3, 3, "3.14", "aa"),
            ("1", 4, 4, "4.14", "bb"),
            ("1", 4, 4, "5.14", "cc"),
            ("1", 5, 5, "6.14", "dd"),
            ("1", 8, 8, "7.14", "ee"),
            ("2", 3, 3, "8.14", "ff")
        ]
        assert list(table.get_records_in_region("1", 4, 5)) == [
            ("1", 4, 4, "4.14", "bb"),
            ("1", 4, 4, "5.14", "cc"),
            ("1", 5, 5, "6.14", "dd")
        ]
        assert list(table.get_records_in_region("1", 4, None)) == [
            ("1", 4, 4, "4.14", "bb"),
            ("1", 4, 4, "5.14", "cc"),
            ("1", 5, 5, "6.14", "dd"),
            ("1", 8, 8, "7.14", "ee")
        ]
        assert list(table.get_records_in_region("1", None, 4)) == [
            ("1", 3, 3, "3.14", "aa"),
            ("1", 4, 4, "4.14", "bb"),
            ("1", 4, 4, "5.14", "cc")
        ]
        assert not list(table.get_records_in_region("1", 20, 25))
        assert list(table.get_records_in_region("2", None, None)) == [
            ("2", 3, 3, "8.14", "ff")
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
                        filename: data.bgz
                        scores:
                        - id: c1
                          name: c1
                          type: float
                        - id: c2
                          name: c2
                          type: str""",
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

    with build_genomic_position_table(res, res.config["tabix_table"]) as table:
        assert table.get_column_names() == ("chrom", "pos_begin", "c1", "c2")
        table.jump_threshold = jump_threshold
        assert list(table.get_all_records()) == [
            ("1", 3, 3, "3.14", "aa"),
            ("1", 4, 4, "4.14", "bb"),
            ("1", 4, 4, "5.14", "cc"),
            ("1", 5, 5, "6.14", "dd"),
            ("1", 8, 8, "7.14", "ee"),
            ("2", 3, 3, "8.14", "ff")
        ]
        assert list(table.get_records_in_region("1", 4, 5)) == [
            ("1", 4, 4, "4.14", "bb"),
            ("1", 4, 4, "5.14", "cc"),
            ("1", 5, 5, "6.14", "dd")
        ]
        assert list(table.get_records_in_region("1", 4, None)) == [
            ("1", 4, 4, "4.14", "bb"),
            ("1", 4, 4, "5.14", "cc"),
            ("1", 5, 5, "6.14", "dd"),
            ("1", 8, 8, "7.14", "ee")
        ]
        assert list(table.get_records_in_region("1", None, 4)) == [
            ("1", 3, 3, "3.14", "aa"),
            ("1", 4, 4, "4.14", "bb"),
            ("1", 4, 4, "5.14", "cc")
        ]
        assert not list(table.get_records_in_region("1", 20, 25))
        assert list(table.get_records_in_region("2", None, None)) == [
            ("2", 3, 3, "8.14", "ff")
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
                    filename: data.bgz
                    scores:
                    - id: c1
                      name: c1
                      type: int""",
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

    table = build_genomic_position_table(res, res.config["tabix_table"])
    table.open()
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
                    filename: data.bgz
                    scores:
                    - id: c1
                      name: c1
                      type: int""",
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

    table = build_genomic_position_table(res, res.config["tabix_table"])
    table.open()
    assert table.chrom_column_i == 0
    assert table.pos_begin_column_i == 1
    assert table.pos_end_column_i == 2

    return table


def test_tabix_table_should_use_sequential_seek_forward(tabix_table):
    table = tabix_table
    assert table.get_column_names() == ("chrom", "pos_begin", "c1")

    assert not table._should_use_sequential_seek_forward("1", 1)
    for row in table.get_records_in_region("1", 1, 1):
        print(row)

    assert not table._should_use_sequential_seek_forward("1", 1)

    assert table._should_use_sequential_seek_forward("1", 2)
    assert table._should_use_sequential_seek_forward("1", 3)

    table.jump_threshold = 0
    assert not table._should_use_sequential_seek_forward("1", 3)


def test_regions_tabix_table_should_use_sequential_seek_forward(regions_tabix_table):
    table = regions_tabix_table
    assert table.get_column_names() == ("chrom", "pos_begin", "pos_end", "c1")

    assert not table._should_use_sequential_seek_forward("1", 1)
    for row in table.get_records_in_region("1", 2, 2):
        print(row)

    assert not table._should_use_sequential_seek_forward("1", 1)
    assert not table._should_use_sequential_seek_forward("1", 6)
    assert table._should_use_sequential_seek_forward("1", 11)
    assert table._should_use_sequential_seek_forward("1", 21)

    table.jump_threshold = 0
    assert not table._should_use_sequential_seek_forward("1", 6)
    assert not table._should_use_sequential_seek_forward("1", 11)
    assert not table._should_use_sequential_seek_forward("1", 21)


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
                    filename: data.bgz
                    scores:
                    - id: c1
                      name: c1
                      type: float""",
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

    table = build_genomic_position_table(res, res.config["tabix_table"])
    table.open()
    return table


@pytest.mark.parametrize("pos_beg,pos_end,expected", [
    (1, 1, [("1", 1, 1, "1")]),
    (2, 2, [("1", 2, 2, "2"), ("1", 2, 2, "3")]),
    (3, 3, [("1", 3, 3, "4"), ("1", 3, 3, "5")]),
    (4, 4, [("1", 4, 4, "6"), ("1", 4, 4, "7")]),
    (3, 4, [
        ("1", 3, 3, "4"), ("1", 3, 3, "5"),
        ("1", 4, 4, "6"), ("1", 4, 4, "7")
    ]),
])
def test_tabix_table_multi_get_regions(
        tabix_table_multiline, pos_beg, pos_end, expected):
    table = tabix_table_multiline
    assert table.get_column_names() == ("chrom", "pos_begin", "c1")

    assert not table._should_use_sequential_seek_forward("1", 1)
    for row in table.get_records_in_region("1", 1, 1):
        print(row)

    lines = table.get_records_in_region("1", pos_beg, pos_end)
    lines = list(lines)
    print(lines)
    assert lines == expected


def test_tabix_table_multi_get_regions_partial(tabix_table_multiline):

    table = tabix_table_multiline
    assert table.get_column_names() == ("chrom", "pos_begin", "c1")

    assert not table._should_use_sequential_seek_forward("1", 1)
    for row in table.get_records_in_region("1", 1, 1):
        print(row)

    for index, row in enumerate(table.get_records_in_region("1", 3, 3)):
        print(row)
        if index == 1:
            break

    lines = table.get_records_in_region("1", 3, 3)
    lines = list(lines)
    print(lines)
    assert lines == [("1", 3, 3, "4"), ("1", 3, 3, "5")]


def test_tabix_middle_optimization(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                text_table:
                    filename: data.mem
                tabix_table:
                    filename: data.bgz
                    scores:
                    - id: c1
                      name: c1
                      type: int""",
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

    with build_genomic_position_table(res, res.config["tabix_table"]) as table:
        row = None
        for row in table.get_records_in_region("1", 1, 1):
            assert row == ("1", 1, 1, "1")
            break
        assert row == ("1", 1, 1, "1")

        row = None
        for row in table.get_records_in_region("1", 1, 1):
            assert row == ("1", 1, 1, "1")
        assert row == ("1", 1, 1, "1")

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
                    filename: data.bgz
                    scores:
                    - id: c1
                      name: c1
                      type: int""",
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

    with build_genomic_position_table(res, res.config["tabix_table"]) as table:
        row = None
        for row in table.get_records_in_region("1", 1, 1):
            assert row == ("1", 1, 1, "1")
            break

        row = None
        for row in table.get_records_in_region("1", 1, 1):
            assert row == ("1", 1, 1, "1")

        row = None
        for row in table.get_records_in_region("1", 4, 4):
            print(row)
        assert row == ("1", 4, 8, "2")

        row = None
        for row in table.get_records_in_region("1", 4, 4):
            print(row)
            break
        assert row == ("1", 4, 8, "2")

        row = None
        for row in table.get_records_in_region("1", 5, 5):
            print(row)
            break
        assert row == ("1", 4, 8, "2")


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
                    scores:
                    - id: c1
                      name: c1
                      type: float
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

    with build_genomic_position_table(res, res.config["tabix_table"]) as table:
        rows = None
        rows = list(table.get_records_in_region("chr1", 505637, 505637))
        assert rows == [("chr1", 505637, 505637, "0.009")]

        rows = None
        rows = list(table.get_records_in_region("chr1", 505643, 505646))
        assert rows == [
            ("chr1", 505643, 505643, "0.012"),
            ("chr1", 505644, 505645, "0.006"),
            ("chr1", 505646, 505646, "0.005"),
        ]

        rows = None
        rows = list(table.get_records_in_region("chr1", 505762, 505762))
        assert rows == [
            ("chr1", 505762, 505764, "0.002"),
        ]


def test_buggy_fitcons_e67(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz
                    scores:
                    - id: c1
                      name: c1
                      type: float
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

    with build_genomic_position_table(res, res.config["tabix_table"]) as table:
        rows = None
        rows = list(table.get_records_in_region("5", 180740299, 180740300))
        assert rows == [
            ("5", 180739426, 180742735, "0.065122"),
        ]

        rows = None
        rows = list(table.get_records_in_region("5", 180740301, 180740301))
        assert rows == [
            ("5", 180739426, 180742735, "0.065122"),
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
                    scores:
                    - id: c1
                      name: c1
                      type: float
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

    with build_genomic_position_table(res, res.config["tabix_table"]) as table:
        assert table.jump_threshold == expected
        rows = None
        rows = list(table.get_records_in_region("5", 180740299, 180740300))
        assert rows == [
            ("5", 180739426, 180742735, "0.065122"),
        ]

        rows = None
        rows = list(table.get_records_in_region("5", 180740301, 180740301))
        assert rows == [
            ("5", 180739426, 180742735, "0.065122"),
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
                    scores:
                    - id: c1
                      name: c1
                      type: float
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

    with build_genomic_position_table(res, res.config["tabix_table"]) as table:
        assert table.BUFFER_MAXSIZE == buffer_maxsize
        assert table.jump_threshold == jump_threshold

        rows = None
        rows = list(table.get_records_in_region("5", 180740299, 180740300))
        assert rows == [
            ("5", 180739426, 180742735, "0.065122"),
        ]

        rows = None
        rows = list(table.get_records_in_region("5", 180740301, 180740301))
        assert rows == [
            ("5", 180739426, 180742735, "0.065122"),
        ]

        rows = None
        rows = list(table.get_records_in_region("5", 180740301, 180742735))
        assert rows == [
            ("5", 180739426, 180742735, "0.065122"),
        ]


def test_contig_length():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                scores:
                - id: c2
                  name: c2
                  type: float""",
        "data.mem": """
            chrom pos_begin pos2  c2
            1     10        12    3.14
            1     11        11    4.14
            1     12        10    5.14
            1     12        11    6.13
            2     1         2     0"""})
    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert tab.get_chromosome_length("1") == 13
        assert tab.get_chromosome_length("2") == 2


def test_contig_length_tabix_table(tabix_table):
    assert tabix_table.get_chromosome_length("1") == 13


def test_vcf_autodetect_format(vcf_res_autodetect_format):
    with build_genomic_position_table(
        vcf_res_autodetect_format,
        vcf_res_autodetect_format.config["tabix_table"]
    ) as tab:
        assert isinstance(tab, VCFGenomicPositionTable)
        assert len(tuple(tab.get_all_records())) == 1


def test_vcf_get_all_records(vcf_res):
    with build_genomic_position_table(
        vcf_res, vcf_res.config["tabix_table"]
    ) as tab:
        assert isinstance(tab, VCFGenomicPositionTable)

        results = tuple(tab.get_all_records())
        assert len(results) == 3
        assert results[0][:3] == ("chr1", 5, 5)
        assert results[1][:3] == ("chr1", 15, 15)
        assert results[2][:3] == ("chr1", 30, 30)

        assert results[0].ref == "A"
        assert results[0].alt == "T"
        assert isinstance(results[0].info, pysam.VariantRecordInfo)


def test_vcf_get_records_in_region(vcf_res):
    with build_genomic_position_table(
        vcf_res, vcf_res.config["tabix_table"]
    ) as tab:
        assert not tuple(tab.get_records_in_region("chr1", 1, 4))
        assert not tuple(tab.get_records_in_region("chr1", 6, 14))
        assert not tuple(tab.get_records_in_region("chr1", 31, 42))

        results = tuple(tab.get_records_in_region("chr1", 1, 6))
        assert len(results) == 1
        assert results[0][:3] == ("chr1", 5, 5)
        results = tuple(tab.get_records_in_region("chr1", 14, 31))
        assert len(results) == 2
        assert results[0][:3] == ("chr1", 15, 15)
        assert results[1][:3] == ("chr1", 30, 30)
        results = tuple(tab.get_records_in_region("chr1", 4, 30))
        assert len(results) == 3
        assert results[0][:3] == ("chr1", 5, 5)
        assert results[1][:3] == ("chr1", 15, 15)
        assert results[2][:3] == ("chr1", 30, 30)


def test_vcf_get_info_fields(vcf_res):
    with build_genomic_position_table(
        vcf_res, vcf_res.config["tabix_table"]
    ) as tab:
        results = tuple(tab.get_all_records())
        assert len(results) == 3
        assert results[0][:3] == ("chr1", 5, 5)
        assert results[1][:3] == ("chr1", 15, 15)
        assert results[2][:3] == ("chr1", 30, 30)

        expected = {
            0: {"A": 1, "B": None, "C": ("c11", "c12"), "D": ("d11",)},
            1: {"A": 2, "B": 21, "C": ("c21",), "D": ("d21", "d22")},
            2: {"A": 3, "B": 31, "C": ("c21",), "D": ("d31", "d32")},
        }
        for i, result in enumerate(results):
            for score in "A", "B", "C", "D":
                assert result.info is not None
                assert result.info.get(score) == expected[i][score]


def test_vcf_jump_ahead_optimization_use_sequential(vcf_res):
    """
    First fetch gives us the following lines in the buffer:
    # chr1 5 5
    # chr1 15 15
    We set jump threshold to 6 and request region:
    # chr1 20 35

    Distance between last line in buffer and requested region is:
    # (20 - 15) == 5 < jump_threshold

    Therefore it should sequentially seek forward
    """
    with build_genomic_position_table(
        vcf_res, vcf_res.config["tabix_table"]
    ) as tab:
        tab.jump_threshold = 6
        assert isinstance(tab, VCFGenomicPositionTable)

        assert tab.stats == {}
        tuple(tab.get_records_in_region("chr1", 1, 6))
        assert len(tab.buffer.deque) == 2
        assert tab.stats["yield from tabix"] == 1
        tuple(tab.get_records_in_region("chr1", 20, 35))
        assert len(tab.buffer.deque) == 1
        assert tab.stats["sequential seek forward"] == 1
        assert tab.stats["yield from tabix"] == 1


def test_vcf_jump_ahead_optimization_use_jump(vcf_res):
    """
    Same as previous test, but the jump threshold is now set to 5
    Distance between last line in buffer and requested region is:
    # (20 - 15) == 5 == jump_threshold

    Therefore it should use the jump optimization
    """
    with build_genomic_position_table(
        vcf_res, vcf_res.config["tabix_table"]
    ) as tab:
        tab.jump_threshold = 5
        assert isinstance(tab, VCFGenomicPositionTable)

        assert tab.stats == {}
        tuple(tab.get_records_in_region("chr1", 1, 6))
        assert len(tab.buffer.deque) == 2
        assert tab.stats["yield from tabix"] == 1
        tuple(tab.get_records_in_region("chr1", 20, 35))
        assert len(tab.buffer.deque) == 1
        assert tab.stats["sequential seek forward"] == 0
        assert tab.stats["yield from tabix"] == 2


def test_vcf_multiallelic(vcf_res_multiallelic):
    """
    Test multiallelic variants are read
    as separate lines and assigned proper allele indices.
    """
    with build_genomic_position_table(
        vcf_res_multiallelic,
        vcf_res_multiallelic.config["tabix_table"]
    ) as tab:
        assert isinstance(tab, VCFGenomicPositionTable)

        results = tuple(map(
            lambda r: (*r[:3], r.allele_index),
            tab.get_all_records()
        ))
        assert results == (
            ("chr1", 2, 2, None),
            ("chr1", 5, 5, 0),
            ("chr1", 15, 15, 0),
            ("chr1", 15, 15, 1),
            ("chr1", 30, 30, 0),
            ("chr1", 30, 30, 1),
            ("chr1", 30, 30, 2),
        )

def test_vcf_multiallelic_region(vcf_res_multiallelic):
    """
    Same as previous test, but for a given region.
    """
    with build_genomic_position_table(
        vcf_res_multiallelic,
        vcf_res_multiallelic.config["tabix_table"]
    ) as tab:
        assert isinstance(tab, VCFGenomicPositionTable)

        results = tuple(map(
            lambda r: (*r[:3], r.allele_index),
            tab.get_records_in_region("chr1", 14, 15))
        )
        assert results == (
            ("chr1", 15, 15, 0),
            ("chr1", 15, 15, 1),
        )


def test_vcf_multiallelic_info_fields(vcf_res_multiallelic):
    """
    Test accessing an INFO field for multiallelic variants.
    Should return the correct value for the given allele.
    """
    with build_genomic_position_table(
        vcf_res_multiallelic,
        vcf_res_multiallelic.config["tabix_table"]
    ) as tab:
        assert isinstance(tab, VCFGenomicPositionTable)

        results = list()
        for line in tab.get_all_records():
            results.append(
                (*line[:3],
                line.allele_index,
                line.get("A"),
                line.get("B"),
                line.get("C"),
                line.get("D"))
            )

        # chrom start stop allele_index A B C D
        assert results == [
            ("chr1", 2, 2, None, 0, "1,2,3", "c01", None),
            ("chr1", 5, 5, 0, 1, "11,12,13", "c12", "d11"),
            ("chr1", 15, 15, 0, 2, "21,22", "c22", "d21"),
            ("chr1", 15, 15, 1, 2, "21,22", "c23", "d22"),
            ("chr1", 30, 30, 0, 3, "31", "c32", "d31"),
            ("chr1", 30, 30, 1, 3, "31", "c33", "d32"),
            ("chr1", 30, 30, 2, 3, "31", "c34", "d33"),
        ]


def test_tables_properly_load_scoredefs():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem
                scores:
                - id: c2
                  name: c2
                  type: float""",
        "data.mem": convert_to_tab_separated("""
            chrom pos_begin pos_end  c2
            1     10        12       3.14
        """)})
    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert len(tab.score_definitions) == 1
        assert "c2" in tab.score_definitions
        assert tab.score_definitions["c2"].value_parser is float


def test_mem_tables_can_load_without_scoredefs():
    res = build_test_resource({
        "genomic_resource.yaml": """
            table:
                filename: data.mem""",
        "data.mem": convert_to_tab_separated("""
            chrom pos_begin pos_end  c2
            1     10        12       3.14
        """)})
    with build_genomic_position_table(res, res.config["table"]) as tab:
        assert not tab.score_definitions


def test_tabix_tables_can_load_without_scoredefs(tmp_path, tabix_file):
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
            #chrom pos_begin pos_end  c2
            1     10        12       3.14
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz"
    )
    with build_genomic_position_table(res, res.config["tabix_table"]) as tab:
        assert not tab.score_definitions


def test_vcf_tables_autogenerate_scoredefs(vcf_res_multiallelic):
    with build_genomic_position_table(
        vcf_res_multiallelic, vcf_res_multiallelic.config["tabix_table"]
    ) as tab:
        assert isinstance(tab, VCFGenomicPositionTable)
        assert set(tab.score_definitions.keys()) == {"A", "B", "C", "D"}
        assert tab.score_definitions["A"].desc == "Score A"
        assert tab.score_definitions["A"].value_parser is None


def test_vcf_tables_can_override_autogenerated_scoredefs(
    vcf_res_score_conf_override
):
    with build_genomic_position_table(
        vcf_res_score_conf_override,
        vcf_res_score_conf_override.config["tabix_table"]
    ) as tab:
        assert isinstance(tab, VCFGenomicPositionTable)
        assert set(tab.score_definitions.keys()) == {"A"}
        assert tab.score_definitions["A"].desc == "Score A, but overriden"
        assert tab.score_definitions["A"].value_parser is float


def test_line_score_value_parsing(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz
                    scores:
                    - id: c2
                      name: c2
                      type: float
            """,
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom  pos_begin  pos_end    c2
            1     10        12       3.14
            1     15        20       4.14
            1     21        30       5.14
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz")

    with build_genomic_position_table(res, res.config["tabix_table"]) as tab:
        assert list(map(lambda l: l.get_score("c2"), tab.get_all_records())) == [
            3.14,
            4.14,
            5.14,
        ]


def test_line_score_na_values(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz
                    scores:
                    - id: c2
                      name: c2
                      type: float
                      na_values:
                      - "4.14"
                      - "5.14"
            """,
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom  pos_begin  pos_end    c2
            1     10        12       3.14
            1     15        20       4.14
            1     21        30       5.14
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz")

    with build_genomic_position_table(res, res.config["tabix_table"]) as tab:
        assert list(map(lambda l: l.get_score("c2"), tab.get_all_records())) == [
            3.14,
            None,
            None,
        ]


def test_line_get_available_score_columns(vcf_res_multiallelic):
    with build_genomic_position_table(
        vcf_res_multiallelic, vcf_res_multiallelic.config["tabix_table"]
    ) as tab:
        assert isinstance(tab, VCFGenomicPositionTable)
        line = next(tab.get_all_records())
        assert set(line.get_available_scores()) == {"A", "B", "C", "D"}


def test_vcf_tuple_scores_autoconcat_to_string(vcf_res_multiallelic):
    with build_genomic_position_table(
        vcf_res_multiallelic, vcf_res_multiallelic.config["tabix_table"]
    ) as tab:
        assert isinstance(tab, VCFGenomicPositionTable)

        results = tuple(map(
            lambda r: (*r[:3], r.get_score("B")),
            tab.get_all_records()
        ))

        assert results == (
            ("chr1", 2, 2, "1,2,3"),
            ("chr1", 5, 5, "11,12,13"),
            ("chr1", 15, 15, "21,22"),
            ("chr1", 15, 15, "21,22"),
            ("chr1", 30, 30, "31"),
            ("chr1", 30, 30, "31"),
            ("chr1", 30, 30, "31"),
        )


def test_get_ref_alt_nonconfigured_missing(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": """
                tabix_table:
                    filename: data.bgz
                    scores:
                    - id: c2
                      name: c2
                      type: float
                      na_values:
                      - "4.14"
                      - "5.14"
            """,
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom  pos_begin  pos_end    c2
            1     10        12       3.14
            1     15        20       4.14
            1     21        30       5.14
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz")

    with build_genomic_position_table(res, res.config["tabix_table"]) as tab:
        results = tuple(map(lambda l: (l.ref, l.alt), tab.get_all_records()))
        assert results == (
            (None, None),
            (None, None),
            (None, None),
        )


def test_get_ref_alt_nonconfigured_existing(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": f"""
                tabix_table:
                    filename: data.bgz
                    scores:
                    - id: c2
                      name: c2
                      type: float
                      na_values:
                      - "4.14"
                      - "5.14"
            """,
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom  pos_begin  pos_end  ref  alt    c2
            1     10        12       A      G       3.14
            1     15        20       A      T       4.14
            1     21        30       A      C       5.14
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz")

    with build_genomic_position_table(res, res.config["tabix_table"]) as tab:
        results = tuple(map(lambda l: (l.ref, l.alt), tab.get_all_records()))
        assert results == (
            (None, None),
            (None, None),
            (None, None),
        )


def test_get_ref_alt_configured_existing(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": f"""
                tabix_table:
                    filename: data.bgz
                    reference:
                      name: reference
                    alternative:
                      name: alternative
                    scores:
                    - id: c2
                      name: c2
                      type: float
            """,
        })

    tabix_to_resource(
        tabix_file(
            """
            #chrom  pos_begin  pos_end  reference  alternative    c2
            1     10        12       A      G       3.14
            1     15        20       A      T       4.14
            1     21        30       A      C       5.14
            """, seq_col=0, start_col=1, end_col=2),
        res, "data.bgz")

    with build_genomic_position_table(res, res.config["tabix_table"]) as tab:
        results = tuple(map(lambda l: (l.ref, l.alt), tab.get_all_records()))
        assert results == (
            ("A", "G"),
            ("A", "T"),
            ("A", "C"),
        )


def test_vcf_get_missing_alt(vcf_res_multiallelic):
    with build_genomic_position_table(
        vcf_res_multiallelic, vcf_res_multiallelic.config["tabix_table"]
    ) as tab:
        assert isinstance(tab, VCFGenomicPositionTable)

        no_alt_line = next(tab.get_all_records())
        assert no_alt_line.ref == "A"
        assert no_alt_line.alt is None


def test_score_definition_via_index_headerless_tabix(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": f"""
                tabix_table:
                    filename: data.bgz
                    header_mode: none
                    chrom:
                      index: 0
                    pos_begin:
                      index: 1
                    pos_end:
                      index: 2
                    scores:
                    - id: piscore
                      index: 3
                      type: float
            """,
        })
    tabix_to_resource(
        tabix_file("1     10        12       3.14",
                   seq_col=0, start_col=1, end_col=2),
        res, "data.bgz"
    )
    with build_genomic_position_table(res, res.config["tabix_table"]) as tab:
        line = next(tab.get_all_records())
        assert len(tab.score_definitions) == 1
        assert "piscore" in tab.score_definitions
        assert line.get_available_scores() == ("piscore",)
        assert line.get_score("piscore") == 3.14



def test_score_definition_list_header_tabix(tmp_path, tabix_file):
    res = build_test_resource(
        scheme="file",
        root_path=str(tmp_path),
        content={
            "genomic_resource.yaml": f"""
                tabix_table:
                    filename: data.bgz
                    header_mode: list
                    header: ["chrom", "start", "stop", "reference", "alt", "score"]
                    pos_begin:
                      name: start
                    pos_end:
                      name: stop
                    reference:
                      name: reference
                    alternative:
                      name: alt
                    scores:
                    - id: piscore
                      name: score
                      type: float
            """,
        })
    tabix_to_resource(
        tabix_file("1     10        12         A         G     3.14",
                   seq_col=0, start_col=1, end_col=2),
        res, "data.bgz"
    )
    with build_genomic_position_table(res, res.config["tabix_table"]) as tab:
        line = next(tab.get_all_records())
        assert len(tab.score_definitions) == 1
        assert "piscore" in tab.score_definitions
        assert line.get_available_scores() == ("piscore",)
        assert line.chrom == "1"
        assert line.pos_begin == 10
        assert line.pos_end == 12
        assert line.ref == "A"
        assert line.alt == "G"
        assert line.get_score("piscore") == 3.14
