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
#
@pytest.mark.parametrize("variant,pos_aggregator,nuc_aggregator,expected", [
    (("1", 14970, "C", "A"),   "mean", "max", 0.001),

    (("1", 14970, "CC", "C"),  "mean", "max", 0.148),
    (("1", 14970, "CC", "C"),  "max",  "max", 0.4),

    (("1", 14970, "C", "CA"),  "mean", "max", 0.022),
    (("1", 14970, "C", "CA"),  "max",  "max", 0.04),
])
def test_position_score_annotator(
        variant, pos_aggregator, nuc_aggregator, expected):

    sa = Allele.build_vcf_allele(*variant)
    assert sa is not None

    repo = build_genomic_resource_repository({
        "id": "test_annotation",
        "type": "embeded",
        "content": {
            "np_score1": {
                "genomic_resource.yaml":
                """\
                type: NPScore
                table:
                    filename: data.mem
                scores:
                - id: test_raw
                  type: float
                  desc: "test values"
                  name: raw
                """,
                "data.mem": """
                    chrom  pos_begin  reference alternative raw
                    1      14970      C         A           0.001
                    1      14970      C         G           0.002
                    1      14970      C         T           0.004
                    1      14971      C         A           0.01
                    1      14971      C         G           0.02
                    1      14971      C         T           0.04
                    1      14972      T         A           0.1
                    1      14972      T         C           0.2
                    1      14972      T         G           0.4
                """
            }
        }
    })

    pipeline_config = AnnotationPipeline.parse_config(
        textwrap.dedent(f"""
            score_annotators:
            - annotator: np_score
              resource: np_score1
              override:
                attributes:
                - source: test_raw
                  dest: test
                  position_aggregator: {pos_aggregator}
                  nucleotide_aggregator: {nuc_aggregator}
            """)
    )

    pipeline = AnnotationPipeline.build(pipeline_config, repo)

    # pipeline.get_schema -> ["attribute", "type", "resource", "scores"]
    # pipeline.annotate_allele(sa) -> {("a1": v1), "a2": v2}}
    result = pipeline.annotate_allele(sa)

    print(sa, result)
    assert result.get("test") == pytest.approx(expected, rel=1e-2)
