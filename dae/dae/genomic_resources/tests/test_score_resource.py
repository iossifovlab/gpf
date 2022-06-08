# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

from dae.genomic_resources.testing import build_testing_repository
from dae.genomic_resources.test_tools import convert_to_tab_separated


def test_pos_gr(tmp_path):
    repo = build_testing_repository(
        repo_id="testing",
        root_path=str(tmp_path),
        content={
            "t": {
                "genomic_resource.yaml": """
                    refGenome: hg38/bla_bla
                    ttype: PositionScore
                    table:
                        file: data.txt""",
                "data.txt": convert_to_tab_separated("""
                    chr pos c1     c2
                    1   3   3.14   aa
                    1   4   4.14   bb
                    1   4   5.14   cc
                    1   5   6.14   dd
                    1   8   7.14   ee
                    2   3   8.14   ff
                """)
            }
        })
    res = repo.get_resource("t")

    assert {fn for fn, _ in res.get_manifest().get_files()} == {
        "genomic_resource.yaml", "data.txt"}
