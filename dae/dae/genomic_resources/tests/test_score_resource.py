from dae.genomic_resources.embeded_repository import GenomicResourceEmbededRepo


def test_pos_gr():
    repo = GenomicResourceEmbededRepo("b", {
        "genomic_resource.yaml": '''
            refGenome: hg38/bla_bla
            ttype: PositionScore
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
    })
    gr = repo.get_resource("")

    assert {fn for fn, _, _ in gr.get_manifest().get_files()} == {
        "genomic_resource.yaml", "data.txt"}
