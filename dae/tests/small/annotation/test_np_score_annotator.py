# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap

import pytest

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    build_inmemory_test_repository,
    setup_directories,
    setup_tabix,
)


#  hg19
#  chrom - 1
#  pos   - 14970
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
            """,
        },
    })

    pipeline_config = textwrap.dedent(f"""
        - np_score:
            resource_id: np_score1
            attributes:
            - source: test_raw
              name: test
              position_aggregator: {pos_aggregator}
              allele_aggregator: {nuc_aggregator}
        """)

    pipeline = load_pipeline_from_yaml(pipeline_config, repo)

    # pipeline.get_schema -> ["attribute", "type", "resource", "scores"]
    # pipeline.annotate_allele(sa) -> {("a1": v1), "a2": v2}}
    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)

    print(annotatable, result)
    assert result.get("test") == pytest.approx(expected, rel=1e-2), annotatable


@pytest.fixture(scope="module")
def np_score2_repo(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("np_score")
    setup_directories(
        root_path / "np_score2", {
        "genomic_resource.yaml": """
            type: np_score
            table:
                filename: data.txt.gz
                format: tabix
                reference:
                  name: ref
                alternative:
                  name: alt
            scores:
                - id: s1
                  type: float
                  name: s1

                - id: s2
                  type: float
                  name: s2
        """,
    })
    setup_tabix(
        root_path / "np_score2" / "data.txt.gz",
        textwrap.dedent("""
            #chrom  pos_begin  ref  alt  s1    s2
            chr1    1          A    G    0.1   1.0
            chr1    1          A    C    0.1   1.0
            chr1    1          A    T    0.1   1.0
            chr1    11         A    G    0.2   2.0
            chr1    11         A    C    0.3   na
            chr1    11         A    T    0.4   na
            chr1    21         C    A    na    3.0
            chr1    21         C    G    na    4.0
            chr1    21         C    T    0.5   5.0
            chr1    31         C    A    na    3.0
            chr1    31         C    G    0.4   na
            chr1    31         C    T    na   5.0

            chr1    41         A    G    0.1   1.0
            chr1    41         A    C    0.1   1.0
            chr1    41         A    G    0.1   1.0

            chr1    51         A    G    0.3   3.0
            chr1    51         A    C    0.33  3.3

            chr1    60         A    G    0.3   3.0
            chr1    60         A    C    0.33  3.3
            chr1    60         A    G    0.4   4.0
            chr1    60         A    C    0.44  4.4

        """).strip(),
        seq_col=0, start_col=1, end_col=1, line_skip=1)
    return build_filesystem_test_repository(root_path)


@pytest.mark.parametrize("variant,pos_aggregator,nuc_aggregator,s1,s2", [
    (("chr1", 1, "A", "G"), "max", "max", 0.1, 1.0),
    (("chr1", 60, "A", "G"), "max", "max", 0.3, 3.0),
    (("chr1", 60, "A", "C"), "max", "max", 0.33, 3.3),
])
def test_np_score2_annotator(
    np_score2_repo: GenomicResourceRepo,
    variant: tuple,
    pos_aggregator: str, nuc_aggregator: str,
    s1: float,
    s2: float,
) -> None:

    pipeline_config = textwrap.dedent(f"""
        - np_score:
            resource_id: np_score2
            attributes:
            - source: s1
              name: s1
              position_aggregator: {pos_aggregator}
              allele_aggregator: {nuc_aggregator}
            - source: s2
              name: s2
              position_aggregator: {pos_aggregator}
              allele_aggregator: {nuc_aggregator}
        """)

    pipeline = load_pipeline_from_yaml(pipeline_config, np_score2_repo)

    # pipeline.get_schema -> ["attribute", "type", "resource", "scores"]
    # pipeline.annotate_allele(sa) -> {("a1": v1), "a2": v2}}
    annotatable = VCFAllele(*variant)
    assert annotatable is not None

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)

    assert result.get("s1") == pytest.approx(s1, rel=1e-2), annotatable
    assert result.get("s2") == pytest.approx(s2, rel=1e-2), annotatable
