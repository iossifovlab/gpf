# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import textwrap

import pytest

from dae.annotation.annotatable import Region
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import build_inmemory_test_repository


@pytest.fixture()
def fixture_repo() -> GenomicResourceRepo:
    repo = build_inmemory_test_repository({
        "position_score1": {
            "genomic_resource.yaml": textwrap.dedent("""
            type: position_score
            table:
                filename: data.mem
            scores:
            - id: test100way
              type: float
              desc: "test values"
              name: 100way
            default_annotation:
                attributes:
                - source: test100way
                  name: test100
            """),
            "data.mem": """
                chrom  pos_begin  pos_end  100way
                chr1   10         19       1.0
                chr1   20         29       2.0
                chr1   30         39       3.0
            """,
        },
        "np_score1": {
            "genomic_resource.yaml": textwrap.dedent("""
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
            """),
            "data.mem": """
                chrom  pos_begin  reference  alternative  raw
                chr1   10         A          C            0.00001
                chr1   10         A          G            0.00002
                chr1   10         A          T            0.00004
                chr1   11         C          A            0.0001
                chr1   11         C          G            0.0002
                chr1   11         C          T            0.0004
                chr1   12         C          A            0.001
                chr1   12         C          G            0.002
                chr1   12         C          T            0.004
                chr1   13         C          A            0.01
                chr1   13         C          G            0.02
                chr1   13         C          T            0.04
                chr1   14         T          A            0.1
                chr1   14         T          C            0.2
                chr1   14         T          G            0.4
            """,
        },
        "allele_score1": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: allele_score
                table:
                    filename: data.mem
                    pos_begin:
                      name: pos_begin
                    reference:
                      name: reference
                    alternative:
                      name: alternative
                scores:
                - id: score
                  name: score
                  type: float
            """),
            "data.mem": """
                chrom  pos_begin  reference  alternative  score
                chr1   10         A          C            0.00001
                chr1   10         A          G            0.00002
                chr1   11         A          T            0.00004
                chr1   11         C          A            0.0001
                chr1   12         C          A            0.001
                chr1   12         C          G            0.002
                chr1   13         C          A            0.01
                chr1   13         C          G            0.02
                chr1   14         T          A            0.1
                chr1   14         T          C            0.2
            """,
        },
    })

    return repo


@pytest.mark.parametrize("region,pos_aggregator, expected", [
    (("chr1", 10, 29), "mean", 1.5),
    (("chr1", 10, 29), "min", 1.0),
    (("chr1", 10, 29), "max", 2.0),

])
def test_position_score_annotator(
        region: tuple, pos_aggregator: str, expected: float,
        fixture_repo: GenomicResourceRepo) -> None:

    annotatable = Region(*region)

    pipeline_config = textwrap.dedent(f"""
            - position_score:
                resource_id: position_score1
                attributes:
                - source: test100way
                  name: test100
                  position_aggregator: {pos_aggregator}
            """)

    pipeline = load_pipeline_from_yaml(pipeline_config, fixture_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)

        print(annotatable, result)
        assert result.get("test100") == expected


@pytest.mark.parametrize("region,pos_aggregator,nuc_aggregator,expected", [
    (("chr1", 10, 13), "max", "max", 0.04),
    (("chr1", 10, 13), "min", "min", 0.00001),
    (("chr1", 10, 14), "max", "min", 0.1),
])
def test_np_score_annotator(
        region: tuple,
        pos_aggregator: str, nuc_aggregator: str, expected: float,
        fixture_repo: GenomicResourceRepo) -> None:

    annotatable = Region(*region)

    pipeline_config = textwrap.dedent(f"""
        - np_score:
            resource_id: np_score1
            attributes:
            - source: test_raw
              name: test
              position_aggregator: {pos_aggregator}
              nucleotide_aggregator: {nuc_aggregator}
        """)

    pipeline = load_pipeline_from_yaml(pipeline_config, fixture_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)

    print(annotatable, result)
    assert result["test"] == expected, annotatable


@pytest.mark.parametrize("region,pos_aggregator,nuc_aggregator,expected", [
    (("chr1", 10, 12), "max", "max", 0.004),
    (("chr1", 10, 13), "min", "min", None),
    (("chr1", 10, 14), "max", "min", None),
])
def test_np_score_annotator_region_length_cutoff(
        region: tuple,
        pos_aggregator: str, nuc_aggregator: str, expected: float,
        fixture_repo: GenomicResourceRepo) -> None:

    annotatable = Region(*region)

    pipeline_config = textwrap.dedent(f"""
        - np_score:
            resource_id: np_score1
            region_length_cutoff: 3
            attributes:
            - source: test_raw
              name: test
              position_aggregator: {pos_aggregator}
              nucleotide_aggregator: {nuc_aggregator}
        """)

    pipeline = load_pipeline_from_yaml(pipeline_config, fixture_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)

    print(annotatable, result)
    assert result["test"] == expected, annotatable


@pytest.mark.parametrize("region,pos_aggregator,allele_aggregator,expected", [
    (("chr1", 10, 13), "max", "max", 0.02),
    (("chr1", 10, 13), "min", "min", 0.00001),
    (("chr1", 10, 14), "max", "min", 0.1),
])
def test_allele_score_annotator(
        region: tuple,
        pos_aggregator: str, allele_aggregator: str, expected: float,
        fixture_repo: GenomicResourceRepo) -> None:

    annotatable = Region(*region)

    pipeline_config = textwrap.dedent(f"""
        - allele_score:
            resource_id: allele_score1
            attributes:
            - source: score
              name: test
              position_aggregator: {pos_aggregator}
              allele_aggregator: {allele_aggregator}
        """)

    pipeline = load_pipeline_from_yaml(pipeline_config, fixture_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(annotatable)

    print(annotatable, result)
    assert result.get("test") == expected, annotatable
