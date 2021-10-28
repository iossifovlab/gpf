import pytest
import textwrap

from dae.variants.core import Allele
from dae.genomic_resources import build_genomic_resource_repository

from dae.annotation.annotation_pipeline import AnnotationPipeline


#  hg19
#  chrom: 1
#  pos:   14970
#
#  C    C    T    T    G    C    G
#  70   71   72   73   74   75   76
#  0.1  0.1  0.2  0.2  0.3  0.3  0.4
#
@pytest.mark.parametrize("variant,pos_aggregator, expected", [
    (("1", 14970, "C", "A"),   "mean", 0.1),

    (("1", 14970, "CC", "C"),  "mean", 0.13),
    (("1", 14970, "CC", "C"),  "max", 0.2),

    (("1", 14970, "CCT", "C"), "mean", 0.15),
    (("1", 14970, "CCT", "C"), "max", 0.2),

    (("1", 14970, "C", "CA"),  "mean", 0.1),
    (("1", 14970, "C", "CAA"), "mean", 0.1),
    (("1", 14970, "C", "CAA"), "max", 0.1),

    (("1", 14971, "C", "CA"),  "mean", 0.15),
    (("1", 14971, "C", "CA"),  "max", 0.2),

    (("1", 14971, "C", "CAA"), "mean", 0.15),
    (("1", 14971, "C", "CAA"), "max", 0.2),
])
def test_position_score_annotator(variant, pos_aggregator, expected):

    sa = Allele.build_vcf_allele(*variant)
    assert sa is not None

    repo = build_genomic_resource_repository({
        "id": "test_annotation",
        "type": "embeded",
        "content": {
            "position_score1": {
                "genomic_resource.yaml":
                """\
                type: PositionScore
                table:
                    filename: data.mem
                scores:
                - id: test100way
                  type: float
                  desc: "test values"
                  name: 100way
                """,
                "data.mem": """
                    chrom  pos_begin  pos_end  100way
                    1      14970      14971    0.1
                    1      14972      14973    0.2
                    1      14974      14975    0.3
                    1      14976      14977    0.4
                """
            }
        }
    })

    pipeline_config = AnnotationPipeline.parse_config(
        textwrap.dedent(f"""
            score_annotators:
            - annotator: position_score
              resource: position_score1
              override:
                attributes:
                - source: test100way
                  dest: test100
                  position_aggregator: {pos_aggregator}
            """)
        )

    pipeline = AnnotationPipeline.build(pipeline_config, repo)

    result = pipeline.annotate_allele(sa)

    print(sa, result)
    assert result.get("test100") == pytest.approx(expected, abs=1e-2)
