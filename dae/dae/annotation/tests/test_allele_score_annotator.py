# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pytest

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import AnnotationPipeline, AnnotatorInfo
from dae.annotation.score_annotator import AlleleScoreAnnotator
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import (
    GR_CONF_FILE_NAME,
    GenomicResourceRepo,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    convert_to_tab_separated,
    setup_directories,
    setup_vcf,
)


def test_allele_score_annotator_attributes(
        grr_fixture: GenomicResourceRepo) -> None:

    pipeline = AnnotationPipeline(grr_fixture)
    annotator = AlleleScoreAnnotator(
        pipeline, AnnotatorInfo("allele_score", [],
                                {"resource_id": "hg38/TESTFreq"}))
    pipeline.add_annotator(annotator)

    assert not annotator.is_open()

    attributes = annotator.get_info().attributes
    assert len(attributes) == 2
    assert attributes[0].name == "alt_freq"
    assert attributes[0].source == "altFreq"
    assert attributes[0].type == "float"
    assert attributes[0].description == ""

    assert attributes[1].name == "alt_freq2"
    assert attributes[1].source == "altFreq2"
    assert attributes[1].type == "float"
    assert attributes[1].description == ""


@pytest.mark.parametrize("variant, expected", [
    (("1", 10, "A", "G"), 0.02),
    (("1", 10, "A", "C"), 0.03),
    (("1", 10, "A", "T"), 0.04),
    (("1", 16, "C", "T"), 0.04),
    (("1", 16, "C", "A"), 0.05),
])
def test_allele_score_with_default_score_annotation(
        variant: tuple, expected: float,
        tmp_path: pathlib.Path) -> None:
    root_path = tmp_path
    setup_directories(
        root_path / "grr", {
            "allele_score": {
                GR_CONF_FILE_NAME: """
                    type: allele_score
                    table:
                        filename: data.txt
                        reference:
                          name: reference
                        alternative:
                          name: alternative
                    scores:
                        - id: ID
                          type: str
                          desc: "variant ID"
                          name: ID
                        - id: freq
                          type: float
                          desc: ""
                          name: freq
                    default_annotation:
                    - source: freq
                      name: allele_freq

                """,
                "data.txt": convert_to_tab_separated("""
                    chrom  pos_begin  reference  alternative ID  freq
                    1      10         A          G           ag  0.02
                    1      10         A          C           ac  0.03
                    1      10         A          T           at  0.04
                    1      16         CA         G           .   0.03
                    1      16         C          T           ct  0.04
                    1      16         C          A           ca  0.05
                """),
            },
        })
    local_repo = build_genomic_resource_repository({
        "id": "allele_score_local",
        "type": "directory",
        "directory": str(root_path / "grr"),
    })
    annotation_configuration = textwrap.dedent("""
        - allele_score:
            resource_id: allele_score
    """)
    pipeline = build_annotation_pipeline(
        pipeline_config_str=annotation_configuration,
        grr_repository=local_repo)

    annotatable = VCFAllele(*variant)
    result = pipeline.annotate(annotatable)
    assert len(result) == 1
    assert result["allele_freq"] == expected


@pytest.mark.parametrize("allele, expected", [
    (("chr1", 1, "C", "A"), 0.001),
    (("chr1", 11, "C", "A"), 0.1),
    (("chr1", 21, "C", "A"), 0.2),
])
def test_allele_annotator_add_chrom_prefix_vcf_table(
        tmp_path: pathlib.Path, allele: tuple, expected: float) -> None:

    setup_directories(
        tmp_path, {
            "allele_score1": {
                "genomic_resource.yaml": textwrap.dedent("""
                    type: allele_score
                    table:
                        filename: data.vcf.gz
                        format: vcf_info
                        chrom_mapping:
                            add_prefix: chr
                    scores:
                    - id: test100way
                      type: float
                      desc: "test values"
                      name: test100way
                    """),
            },
        })

    setup_vcf(
        tmp_path / "allele_score1" / "data.vcf.gz",
        textwrap.dedent("""
        ##fileformat=VCFv4.1
        ##INFO=<ID=test100way,Number=1,Type=Float,Description="test values">
        ##contig=<ID=1>
        #CHROM POS ID REF ALT QUAL FILTER INFO
        1      1   .  C   A   .    .      test100way=0.001;
        1      11  .  C   A   .    .      test100way=0.1;
        1      21  .  C   A   .    .      test100way=0.2;
        """))
    repo = build_filesystem_test_repository(tmp_path)

    pipeline_config = textwrap.dedent("""
            - allele_score:
                resource_id: allele_score1
                attributes:
                - source: test100way
            """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=repo)
    with pipeline.open() as work_pipeline:
        annotatable = VCFAllele(*allele)
        result = work_pipeline.annotate(annotatable)

        print(annotatable, result)
        assert result.get("test100way") == pytest.approx(expected, rel=1e-3)
