import pytest

from dae.genomic_resources.genome_position_table import \
    TabixGenomicPositionTable, \
    open_genome_position_table, \
    save_as_tabix_table
from dae.genomic_resources.tabix_helper import TabixHelper

from dae.genomic_resources import build_genomic_resource_repository



@pytest.fixture
def tabix_index(tmp_path):
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
                    1     32000     3
                    1     32001     4
                    2     1         5
                    2     2         6
                    2     64000     7
                    2     64001     8
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


def test_explore_tabix_index(tabix_index):
    table: TabixGenomicPositionTable = tabix_index
    config = table.genomic_resource.get_config()
    print(config)
    print(dir(table.tabix_file))
    print(table.tabix_file.filename)
    print(table.tabix_file.index_filename)
    print(table.tabix_file.filename_index)

    index_filename = table.tabix_file.filename_index.decode("utf8")
    filename = table.tabix_file.filename.decode("utf8")
    print(filename, index_filename)

    helper = TabixHelper(filename, index_filename)
    helper.open()

    helper.load_index()
    helper.close()


# def test_explore_tabixpy(tabix_index):
#     import tabixpy

#     table: TabixGenomicPositionTable = tabix_index

#     filename = table.tabix_file.filename.decode("utf8")
#     tx = tabixpy.Tabix(filename)
#     tx.load()
