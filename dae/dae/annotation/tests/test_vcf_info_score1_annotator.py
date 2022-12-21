# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pytest

from dae.testing import setup_directories, setup_vcf
from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.repository import GenomicResourceProtocolRepo

from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotatable import VCFAllele


@pytest.fixture
def score1_repo(tmp_path_factory):
    vcf_header = """
##fileformat=VCFv4.1
##INFO=<ID=A,Number=1,Type=Integer,Description="Score A">
##INFO=<ID=B,Number=1,Type=Integer,Description="Score B">
##INFO=<ID=C,Number=.,Type=String,Description="Score C">
##INFO=<ID=D,Number=.,Type=String,Description="Score D">
#CHROM POS ID REF ALT QUAL FILTER  INFO
    """
    root_path = tmp_path_factory.mktemp("score1_repo")
    setup_directories(
        root_path / "grr",
        {
            "score1": {
                "genomic_resource.yaml": textwrap.dedent("""
                    type: allele_score
                    table:
                        filename: score1.vcf.gz
                        index_filename: score1.vcf.gz.tbi
                        desc: |
                            Example testing Score1.
            """)
            }
        }
    )
    setup_vcf(
        root_path / "grr" / "score1" / "score1.vcf.gz",
        textwrap.dedent(f"""
{vcf_header}
chrA   1   .  A   T   .    .       A=1;C=c11,c12;D=d11
chrA   2   .  A   T   .    .       A=2;B=21;C=c21;D=d21,d22
chrA   3   .  A   T   .    .       A=3;B=31;C=c21;D=d31,d32
    """)
    )
    setup_vcf(
        root_path / "grr" / "score1" / "score1.header.vcf.gz",
        textwrap.dedent(vcf_header)
    )

    proto = build_fsspec_protocol("testing", str(root_path / "grr"))
    return GenomicResourceProtocolRepo(proto)


def test_vcf_info_annotator_all_attributes(score1_repo):
    pipeline_config = textwrap.dedent("""
            - allele_score:
                resource_id: score1
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=score1_repo)

    annotator = pipeline.annotators[0]
    annotator.score.open()
    attributes = annotator.get_all_annotation_attributes()
    assert len(attributes) == 4

    assert annotator.get_all_annotation_attributes() == [
        {"desc": "Score A", "name": "A", "type": "int"},
        {"desc": "Score B", "name": "B", "type": "int"},
        {"desc": "Score C", "name": "C", "type": "str"},
        {"desc": "Score D", "name": "D", "type": "str"},
    ]

    annotator.open()
    assert annotator.get_all_annotation_attributes() == [
        {"desc": "Score A", "name": "A", "type": "int"},
        {"desc": "Score B", "name": "B", "type": "int"},
        {"desc": "Score C", "name": "C", "type": "str"},
        {"desc": "Score D", "name": "D", "type": "str"},
    ]


def test_vcf_info_default_annotation(score1_repo):
    pipeline_config = textwrap.dedent("""
            - allele_score:
                resource_id: score1
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=score1_repo)

    annotator = pipeline.annotators[0]
    annotator.score.open()
    attributes = annotator.get_annotation_config()
    assert len(attributes) == 4

    assert attributes == [
        {"source": "A", "destination": "A"},
        {"source": "B", "destination": "B"},
        {"source": "C", "destination": "C"},
        {"source": "D", "destination": "D"}
    ]


def test_vcf_info_config_annotation(score1_repo):
    pipeline_config = textwrap.dedent("""
            - allele_score:
                resource_id: score1
                attributes:
                - source: C
                  destination: score1_c
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=score1_repo)

    annotator = pipeline.annotators[0]
    attributes = annotator.get_annotation_config()
    assert len(attributes) == 1

    assert attributes == [
        {"source": "C", "destination": "score1_c", "internal": False},
    ]


@pytest.mark.parametrize("vcf_allele,expected", [
    (
        VCFAllele("chrA", 1, "A", "T"),
        {"score1_a": 1, "score1_b": None,
         "score1_c": "c11,c12", "score1_d": "d11"}
    ),
    (
        VCFAllele("chrA", 1, "A", "C"),
        {"score1_a": None, "score1_b": None,
         "score1_c": None, "score1_d": None}
    ),
    (
        VCFAllele("chrA", 2, "A", "T"),
        {"score1_a": 2, "score1_b": 21,
         "score1_c": "c21", "score1_d": "d21,d22"}
    ),
    (
        VCFAllele("chrA", 2, "A", "C"),
        {"score1_a": None, "score1_b": None,
         "score1_c": None, "score1_d": None}
    ),
])
def test_vcf_info_annotator(
        vcf_allele, expected, score1_repo):

    pipeline_config = textwrap.dedent("""
        - allele_score:
            resource_id: score1
            attributes:
            - source: A
              destination: score1_a
            - source: B
              destination: score1_b
            - source: C
              destination: score1_c
            - source: D
              destination: score1_d
        """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=score1_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(vcf_allele)
        assert result == expected
