# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.genomic_resources import GenomicResource
from dae.genomic_resources.genomic_scores import \
    open_allele_score_from_resource
from dae.genomic_resources.testing import build_test_resource
from dae.genomic_resources.repository import GR_CONF_FILE_NAME


def test_the_simplest_allele_score():
    res: GenomicResource = build_test_resource({
        GR_CONF_FILE_NAME: """
            type: allele_score
            table:
                filename: data.mem
            scores:
                - id: freq
                  type: float
                  desc: ""
                  name: freq
        """,
        "data.mem": """
            chrom  pos_begin  reference  alternative  freq
            1      10         A          G            0.02
            1      10         A          C            0.03
            1      10         A          A            0.04
            1      16         CA         G            0.03
            1      16         C          T            0.04
            1      16         C          A            0.05
        """
    })
    assert res.get_type() == "allele_score"

    score = open_allele_score_from_resource(res)
    assert score.get_all_scores() == ["freq"]
    assert score.fetch_scores("1", 10, "A", "C") == {"freq": 0.03}


def test_allele_score_fetch_region():
    res: GenomicResource = build_test_resource({
        GR_CONF_FILE_NAME: """
            type: allele_score
            table:
                filename: data.mem
            scores:
                - id: freq
                  type: float
                  desc: ""
                  name: freq
        """,
        "data.mem": """
            chrom  pos_begin  reference  alternative  freq
            1      10         A          G            0.02
            1      10         A          C            0.03
            1      10         A          A            0.04
            1      16         CA         G            0.03
            1      16         C          T            0.04
            1      16         C          A            0.05
            2      16         CA         G            0.03
            2      16         C          T            EMPTY
            2      16         C          A            0.05
        """
    })
    score = open_allele_score_from_resource(res)

    # The in-mem table will sort the records. In this example it will sort
    # the alternatives column (previous columns are the same). That is why
    # the scores (freq) appear out of order
    assert list(score.fetch_region("1", 10, 11, ["freq"])) == \
        [{"freq": 0.04},
         {"freq": 0.03},
         {"freq": 0.02}]

    assert list(score.fetch_region("1", 10, 16, ["freq"])) == \
        [{"freq": 0.04},
         {"freq": 0.03},
         {"freq": 0.02},
         {"freq": 0.05},
         {"freq": 0.04},
         {"freq": 0.03}]

    assert list(score.fetch_region("2", None, None, ["freq"])) == \
        [{"freq": 0.05},
         {"freq": None},
         {"freq": 0.03}]
