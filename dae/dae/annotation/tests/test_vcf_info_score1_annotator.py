# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from typing import Optional, Union

import pytest

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.repository import GenomicResourceProtocolRepo
from dae.testing import setup_directories, setup_vcf


@pytest.fixture()
def score1_repo(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceProtocolRepo:
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
            """),
            },
        },
    )
    setup_vcf(
        root_path / "grr" / "score1" / "score1.vcf.gz",
        textwrap.dedent("""
##fileformat=VCFv4.1
##INFO=<ID=A,Number=1,Type=Integer,Description="Score A">
##INFO=<ID=B,Number=1,Type=Integer,Description="Score B">
##INFO=<ID=C,Number=.,Type=String,Description="Score C">
##INFO=<ID=D,Number=.,Type=String,Description="Score D">
#CHROM POS ID REF ALT QUAL FILTER  INFO
chrA   1   .  A   T   .    .       A=1;C=c11,c12;D=d11
chrA   2   .  A   T   .    .       A=2;B=21;C=c21;D=d21,d22
chrA   3   .  A   T   .    .       A=3;B=31;C=c21;D=d31,d32
    """),
    )

    proto = build_fsspec_protocol("testing", str(root_path / "grr"))
    return GenomicResourceProtocolRepo(proto)


def test_vcf_info_annotator_all_attributes(
    score1_repo: GenomicResourceProtocolRepo,
) -> None:

    pipeline = load_pipeline_from_yaml("- allele_score: score1", score1_repo)

    expected_name_scr_type_desc = [
        ("A", "A", "int", "Score A"),
        ("B", "B", "int", "Score B"),
        ("C", "C", "str", "Score C"),
        ("D", "D", "str", "Score D"),
    ]
    observed_name_src_type_desc = \
        [(at.name, at.source, at.type, at.description)
         for at in pipeline.get_attributes()]

    assert observed_name_src_type_desc == expected_name_scr_type_desc


def test_vcf_info_config_annotation(
    score1_repo: GenomicResourceProtocolRepo,
) -> None:

    pipeline = load_pipeline_from_yaml(
        """- allele_score:
                resource_id: score1
                attributes:
                - source: C
                  name: score1_c
        """, score1_repo)

    assert len(pipeline.get_attributes()) == 1
    att = pipeline.get_attributes()[0]

    assert (att.name, att.source, att.internal) == ("score1_c", "C", False)


@pytest.mark.parametrize("vcf_allele,expected", [
    (
        VCFAllele("chrA", 1, "A", "T"),
        {"score1_a": 1, "score1_b": None,
         "score1_c": "c11,c12", "score1_d": "d11"},
    ),
    (
        VCFAllele("chrA", 1, "A", "C"),
        {"score1_a": None, "score1_b": None,
         "score1_c": None, "score1_d": None},
    ),
    (
        VCFAllele("chrA", 2, "A", "T"),
        {"score1_a": 2, "score1_b": 21,
         "score1_c": "c21", "score1_d": "d21,d22"},
    ),
    (
        VCFAllele("chrA", 2, "A", "C"),
        {"score1_a": None, "score1_b": None,
         "score1_c": None, "score1_d": None},
    ),
])
def test_vcf_info_annotator(
    vcf_allele: VCFAllele,
    expected: dict[str, Optional[Union[int, str]]],
    score1_repo: GenomicResourceProtocolRepo,
) -> None:

    pipeline_config = textwrap.dedent("""
        - allele_score:
            resource_id: score1
            attributes:
            - source: A
              name: score1_a
            - source: B
              name: score1_b
            - source: C
              name: score1_c
            - source: D
              name: score1_d
        """)

    pipeline = load_pipeline_from_yaml(pipeline_config, score1_repo)

    with pipeline.open() as work_pipeline:
        result = work_pipeline.annotate(vcf_allele)
        assert result == expected
