# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines

import pathlib

from dae.genomic_resources.genomic_position_table import (
    build_genomic_position_table,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_resource,
    convert_to_tab_separated,
    setup_directories,
    setup_gzip,
)


def test_inmemory_genomic_position_table_tsv(tmp_path: pathlib.Path) -> None:
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            table:
                filename: data.tsv""",
        "data.tsv": convert_to_tab_separated("""
            chrom pos_begin pos2  c2
            1     10        12    3.14
            1     11        11    4.14
        """)})
    res = build_filesystem_test_resource(tmp_path)
    assert res.config is not None
    tab = build_genomic_position_table(
        res, res.config["table"])
    tab.open()
    assert len(list(tab.get_all_records())) == 2


def test_inmemory_genomic_position_table_tsv_compressed(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            table:
                filename: data.tsv.gz""",
    })
    setup_gzip(tmp_path / "data.tsv.gz", """
        chrom pos_begin pos2  c2
        1     10        12    3.14
        1     11        11    4.14
    """)
    res = build_filesystem_test_resource(tmp_path)
    assert res.config is not None
    tab = build_genomic_position_table(
        res, res.config["table"])
    tab.open()
    assert len(list(tab.get_all_records())) == 2


def test_inmemory_genomic_position_table_txt(tmp_path: pathlib.Path) -> None:
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            table:
                filename: data.txt""",
        "data.txt": convert_to_tab_separated("""
            chrom pos_begin pos2  c2
            1     10        12    3.14
            1     11        11    4.14
        """)})
    res = build_filesystem_test_resource(tmp_path)
    assert res.config is not None
    tab = build_genomic_position_table(
        res, res.config["table"])
    tab.open()
    assert len(list(tab.get_all_records())) == 2


def test_inmemory_genomic_position_table_txt_compressed(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            table:
                filename: data.txt.gz""",
    })
    setup_gzip(tmp_path / "data.txt.gz", """
        chrom pos_begin pos2  c2
        1     10        12    3.14
        1     11        11    4.14
    """)
    res = build_filesystem_test_resource(tmp_path)
    assert res.config is not None
    tab = build_genomic_position_table(
        res, res.config["table"])
    tab.open()
    assert len(list(tab.get_all_records())) == 2


def test_inmemory_genomic_position_table_csv(tmp_path: pathlib.Path) -> None:
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            table:
                filename: data.csv""",
        "data.csv": convert_to_tab_separated("""
            chrom,pos_begin,pos2 ,c2
            1,10,12,3.14
            1,11,11,4.14
        """)})
    res = build_filesystem_test_resource(tmp_path)
    assert res.config is not None
    tab = build_genomic_position_table(
        res, res.config["table"])
    tab.open()
    assert len(list(tab.get_all_records())) == 2


def test_inmemory_genomic_position_table_csv_compressed(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            table:
                filename: data.csv.gz""",
    })
    setup_gzip(tmp_path / "data.csv.gz", """
        chrom,pos_begin,pos2 ,c2
        1,10,12,3.14
        1,11,11,4.14
    """)
    res = build_filesystem_test_resource(tmp_path)
    assert res.config is not None
    tab = build_genomic_position_table(
        res, res.config["table"])
    tab.open()
    assert len(list(tab.get_all_records())) == 2


def test_inmemory_genomic_position_table_zero_based_no_header(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            table:
              filename: data.tsv
              header_mode: none
              zero_based: True
              chrom:
                index: 0
              pos_begin:
                index: 1
              pos_end:
                index: 1

        """,
        "data.tsv": convert_to_tab_separated("""
            chr1  0   0.1
            chr1  1   0.2
            chr1  2   0.3
            chr2  0   0.1
            chr2  1   0.2
            chr2  2   0.3
        """)})
    res = build_filesystem_test_resource(tmp_path)
    assert res.config is not None
    table = build_genomic_position_table(res, res.config["table"])
    table.open()
    assert len(list(table.get_all_records())) == 6
    vs = list(table.get_records_in_region("chr1", 2, 2))
    assert len(vs) == 1
    assert vs[0].chrom == "chr1"
    assert vs[0].pos_begin == 2
    assert vs[0].pos_end == 2


def test_get_records_in_region_without_chrom(tmp_path: pathlib.Path) -> None:
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            table:
                filename: data.txt""",
        "data.txt": convert_to_tab_separated("""
            chrom pos_begin pos2  c2
            1     10        12    3.14
            1     11        11    4.14
        """)})
    res = build_filesystem_test_resource(tmp_path)
    assert res.config is not None
    tab = build_genomic_position_table(res, res.config["table"])
    tab.open()
    assert len(list(tab.get_records_in_region())) == 2
