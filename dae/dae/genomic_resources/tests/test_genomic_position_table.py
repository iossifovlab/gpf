import pytest

from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.genome_position_table import \
    get_genome_position_table
from dae.genomic_resources.genome_position_table import \
    save_as_tabix_table


def test_text_table():
    repo = build_genomic_resource_repository(
        {"id": "b", "type": "embeded", "content": {
            "one": {
                "genomic_resource.yaml": '''
                    table:
                        file: data.txt''',
                "data.txt": '''
                    chr pos c1     c2
                    1   3   3.14   aa
                    1   4   4.14   bb
                    1   4   5.14   cc
                    1   5   6.14   dd
                    1   8   7.14   ee
                    2   3   8.14   ff'''
            }
        }
        })
    gr = repo.get_resource("one")
    table = get_genome_position_table(gr, gr.config['table'])
    assert table.get_columns() == ('chr', 'pos', 'c1', 'c2')

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
                        file: data.txt
                    tabix_table:
                        file: data.bgz''',
                "data.txt": '''
                    chr pos c1     c2
                    1   3   3.14   aa
                    1   4   4.14   bb
                    1   4   5.14   cc
                    1   5   6.14   dd
                    1   8   7.14   ee
                    2   3   8.14   ff'''
            }
        }
        })
    d_repo = build_genomic_resource_repository(
        {"id": "d", "type": "directory", "directory": tmp_path})
    d_repo.store_all_resources(e_repo)
    e_gr = e_repo.get_resource("one")
    d_gr = d_repo.get_resource("one")
    save_as_tabix_table(
        get_genome_position_table(e_gr, e_gr.config['text_table']),
        str(d_repo.get_file_path(d_gr, "data.bgz")))

    table = get_genome_position_table(d_gr, d_gr.config['tabix_table'])
    assert table.get_columns() == ('chr', 'pos', 'c1', 'c2')

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
