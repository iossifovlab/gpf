# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.genomic_resources.repository import GenomicResource, GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_test_resource


def test_default_annotation_pre_normalize_validates():
    res: GenomicResource = build_test_resource({
        GR_CONF_FILE_NAME: """
            type: position_score
            table:
                filename: data.mem
            scores:
              - id: phastCons100way
                type: float
                desc: "The phastCons computed over the tree of 100 \
                       verterbarte species"
                name: s1
            default_annotation:
              attributes:
                - phastCons100way""",
        "data.mem": """
            chrom  pos_begin  s1
            1      10         0.02
            1      11         0.03
            1      15         0.46
            2      8          0.01
            """
    })
    assert res is not None
    assert res.get_type() == "position_score"
