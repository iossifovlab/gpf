# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap

import pytest

from dae.genomic_resources.testing import build_inmemory_test_repository

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import build_annotation_pipeline


#  hg19
#  chrom: 1
#  pos:   14970
#
#  T   A   C   C    C    T    T    G    C    G
#  67  68  69  70   71   72   73   74   75   76
#
@pytest.mark.parametrize("variant,pos_aggregator,nuc_aggregator,expected", [
    (("1", 14970, "C", "A"), "mean", "max", 0.001),

    (("1", 14970, "CA", "C"), "mean", "max", (0.004 + 0.04 + 0.4) / 3),
    (("1", 14970, "CA", "C"), "max", "max", 0.4),

    (("1", 14970, "C", "CA"), "mean", "max", 0.022),
    (("1", 14970, "C", "CA"), "max", "max", 0.04),
])
def test_np_score_annotator(
        variant: tuple,
        pos_aggregator: str, nuc_aggregator: str, expected: float) -> None:

    annotatable = VCFAllele(*variant)
    assert annotatable is not None
    print(annotatable)
    repo = build_inmemory_test_repository({
        "np_score1": {
            "genomic_resource.yaml":
            """\
            type: np_score
            table:
                filename: data.mem
                reference:
                  name: reference
                alternative:
                  name: alternative
            scores:
            - id: test_raw
              type: float
              desc: "test values"
              name: raw
            """,
            "data.mem": """
                chrom  pos_begin  reference alternative raw
                1      14968      A         C           0.00001
                1      14968      A         G           0.00002
                1      14968      A         T           0.00004
                1      14969      C         A           0.0001
                1      14969      C         G           0.0002
                1      14969      C         T           0.0004
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
    })

    pipeline_config = textwrap.dedent(f"""
        - np_score:
            resource_id: np_score1
            attributes:
            - source: test_raw
              destination: test
              position_aggregator: {pos_aggregator}
              nucleotide_aggregator: {nuc_aggregator}
        """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config, grr_repository=repo)

    # pipeline.get_schema -> ["attribute", "type", "resource", "scores"]
    # pipeline.annotate_allele(sa) -> {("a1": v1), "a2": v2}}
    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)

    print(annotatable, result)
    assert result.get("test") == pytest.approx(expected, rel=1e-2), annotatable
