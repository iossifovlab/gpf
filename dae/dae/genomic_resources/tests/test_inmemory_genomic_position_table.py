# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines

from dae.genomic_resources.testing import \
    setup_directories, convert_to_tab_separated, setup_gzip, \
    build_filesystem_test_resource
from dae.genomic_resources.genome_position_table import \
    open_genome_position_table


def test_inmemory_genomic_position_table_tsv(tmp_path):
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
    tab = open_genome_position_table(
        res, res.config["table"])
    assert len(list(tab.get_all_records())) == 2


def test_inmemory_genomic_position_table_tsv_compressed(tmp_path):
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            table:
                filename: data.tsv.gz"""
    })
    setup_gzip(tmp_path / "data.tsv.gz", """
        chrom pos_begin pos2  c2
        1     10        12    3.14
        1     11        11    4.14
    """)
    res = build_filesystem_test_resource(tmp_path)
    tab = open_genome_position_table(
        res, res.config["table"])
    assert len(list(tab.get_all_records())) == 2


def test_inmemory_genomic_position_table_txt(tmp_path):
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
    tab = open_genome_position_table(
        res, res.config["table"])
    assert len(list(tab.get_all_records())) == 2


def test_inmemory_genomic_position_table_txt_compressed(tmp_path):
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            table:
                filename: data.txt.gz"""
    })
    setup_gzip(tmp_path / "data.txt.gz", """
        chrom pos_begin pos2  c2
        1     10        12    3.14
        1     11        11    4.14
    """)
    res = build_filesystem_test_resource(tmp_path)
    tab = open_genome_position_table(
        res, res.config["table"])
    assert len(list(tab.get_all_records())) == 2


def test_inmemory_genomic_position_table_csv(tmp_path):
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
    tab = open_genome_position_table(
        res, res.config["table"])
    assert len(list(tab.get_all_records())) == 2


def test_inmemory_genomic_position_table_csv_compressed(tmp_path):
    setup_directories(tmp_path, {
        "genomic_resource.yaml": """
            table:
                filename: data.csv.gz"""
    })
    setup_gzip(tmp_path / "data.csv.gz", """
        chrom,pos_begin,pos2 ,c2
        1,10,12,3.14
        1,11,11,4.14
    """)
    res = build_filesystem_test_resource(tmp_path)
    tab = open_genome_position_table(
        res, res.config["table"])
    assert len(list(tab.get_all_records())) == 2
