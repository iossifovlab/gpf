# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pathlib
import textwrap

import pytest

from dae.annotation.annotation_config import (
    AnnotationConfigParser,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPreambule,
    AnnotatorInfo,
    AttributeInfo,
)
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.testing import convert_to_tab_separated, setup_directories


@pytest.fixture()
def test_grr(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    root_path = tmp_path
    setup_directories(
        root_path, {
            "grr.yaml": textwrap.dedent(f"""
                id: reannotation_repo
                type: dir
                directory: "{root_path}/grr"
            """),
            "grr": {
                "dummy_genome": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: reference_genome
                        filename: genome.fa
                    """),
                    "genome.fa": """blabla""",
                },
                "score_one": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score
                          type: float
                          name: s1
                        meta:
                            labels:
                                foo: ALPHA
                                bar: GAMMA
                                baz: sub_one
                    """),
                    "data.txt": convert_to_tab_separated("""
                        chrom  pos_begin  s1
                        foo    1          0.1
                    """),
                },
                "score_two": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score
                          type: float
                          name: s2
                        meta:
                            labels:
                                foo: BETA
                                bar: GAMMA
                                baz: sub_two
                    """),
                    "data.txt": convert_to_tab_separated("""
                        chrom  pos_begin  s2
                        foo    1          0.2
                    """),
                },
                "score_three": {
                    "genomic_resource.yaml": textwrap.dedent("""
                        type: np_score
                        table:
                            filename: data.txt
                            reference:
                              name: ref
                            alternative:
                              name: alt
                        scores:
                            - id: s3
                              name: s3
                              type: float
                              desc: ""
                    """),
                    "data.txt": convert_to_tab_separated("""
                        chrom  pos_begin  ref  alt  s3
                        foo    1          A    G    0.2
                    """),
                },
                "scores": {
                    "scoredir_one": {
                        "subscore": {
                            "genomic_resource.yaml": textwrap.dedent("""
                                type: position_score
                                table:
                                    filename: data.txt
                                scores:
                                - id: score
                                  type: float
                                  name: s1
                                meta:
                                    labels:
                                        foo: ALPHA
                                        bar: DELTA
                            """),
                            "data.txt": convert_to_tab_separated("""
                                chrom  pos_begin  s1
                                foo    1          0.1
                            """),
                        },
                    },
                    "scoredir_two": {
                        "subscore": {
                            "genomic_resource.yaml": textwrap.dedent("""
                                type: position_score
                                table:
                                    filename: data.txt
                                scores:
                                - id: score
                                  type: float
                                  name: s2
                                meta:
                                    labels:
                                        foo: BETA
                                        bar: DELTA
                            """),
                            "data.txt": convert_to_tab_separated("""
                                chrom  pos_begin  s2
                                foo    1          0.2
                            """),
                        },
                    },
                    "scoredir_three": {
                        "subscore": {
                            "genomic_resource.yaml": textwrap.dedent("""
                                type: np_score
                                table:
                                    filename: data.txt
                                    reference:
                                      name: ref
                                    alternative:
                                      name: alt
                                scores:
                                    - id: s3
                                      name: s3
                                      type: float
                                      desc: ""
                            """),
                            "data.txt": convert_to_tab_separated("""
                                chrom  pos_begin  ref  alt  s3
                                foo    1          A    G    0.2
                            """),
                        },
                    },
                },
            },
        },
    )
    return build_genomic_resource_repository(file_name=str(
        root_path / "grr.yaml",
    ))


def test_simple_annotator_simple() -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - annotator:
            resource_id: resource
    """)

    assert pipeline_config == [
        AnnotatorInfo("annotator", [], {"resource_id": "resource"},
                      annotator_id="A0"),
    ]


def test_short_annotator_config() -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - annotator: resource
    """)

    assert pipeline_config == [
        AnnotatorInfo(
            "annotator", [], {"resource_id": "resource"}, annotator_id="A0",
        ),
    ]


def test_minimal_annotator_config() -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - annotator
    """)
    assert pipeline_config == [
        AnnotatorInfo("annotator", [], {}, annotator_id="A0"),
    ]


def test_annotator_config_with_more_parameters() -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - annotator:
                resource_id: resource
                key: value
    """)

    assert pipeline_config == [
        AnnotatorInfo(
            "annotator", [], {"resource_id": "resource", "key": "value"},
            annotator_id="A0",
        ),
    ]


def test_annotator_config_with_attributes() -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
            - annotator:
                attributes:
                - att1
                - name: att2
                - name: att3
                  source: some_score
                - name: att4
                  source: some_score
                  att_param: foo
                - name: att5
                  att_param: raz
                  internal: true
                - source: att6
    """)

    assert pipeline_config == \
        [AnnotatorInfo("annotator", [
            AttributeInfo("att1", "att1", False, {}),
            AttributeInfo("att2", "att2", False, {}),
            AttributeInfo("att3", "some_score", False, {}),
            AttributeInfo("att4", "some_score", False, {"att_param": "foo"}),
            AttributeInfo("att5", "att5", True, {"att_param": "raz"}),
            AttributeInfo("att6", "att6", False, {})],
            {}, annotator_id="A0")]


def test_annotator_config_with_params_and_attributes() -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - annotator:
            resource_id: resource
            attributes:
            - att1
            - att2
    """)

    assert pipeline_config == \
        [AnnotatorInfo("annotator", [
            AttributeInfo("att1", "att1", False, {}),
            AttributeInfo("att2", "att2", False, {}),
        ], {
            "resource_id": "resource",
        }, annotator_id="A0")]


def test_empty_config() -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("")

    # pylint: disable=use-implicit-booleaness-not-comparison
    assert pipeline_config == []


def test_effect_annotator_extra_attributes() -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - effect_annotator:
            gene_models: hg38/gene_models/refSeq_20200330
            genome: hg38/genomes/GRCh38-hg38
            promoter_len: 100
            attributes:
            - source: genes
              name: list_of_genes
              format: list
              internal: yes
            - source: genes
              format: str
            - source: genes_LGD
            - genes_missense
    """)

    assert pipeline_config == [
        AnnotatorInfo("effect_annotator", [
            AttributeInfo("list_of_genes", "genes", True, {"format": "list"}),
            AttributeInfo("genes", "genes", False, {"format": "str"}),
            AttributeInfo("genes_LGD", "genes_LGD", False, {}),
            AttributeInfo("genes_missense", "genes_missense", False, {})], {
            "gene_models": "hg38/gene_models/refSeq_20200330",
            "genome": "hg38/genomes/GRCh38-hg38",
            "promoter_len": 100}, annotator_id="A0",
        ),
    ]


def test_wildcard_basic(test_grr: GenomicResourceRepo) -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - position_score: score_*
    """, grr=test_grr)
    assert pipeline_config == [
        AnnotatorInfo(
            "position_score", [], {"resource_id": "score_one"},
            annotator_id="A0_score_one",
        ),
        AnnotatorInfo(
            "position_score", [], {"resource_id": "score_two"},
            annotator_id="A0_score_two",
        ),
    ]


def test_wildcard_directory(test_grr: GenomicResourceRepo) -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - position_score: "scores/**/subscore"
    """, grr=test_grr)
    assert pipeline_config == [
        AnnotatorInfo(
            "position_score", [],
            {"resource_id": "scores/scoredir_one/subscore"},
            annotator_id="A0_scores/scoredir_one/subscore",
        ),
        AnnotatorInfo(
            "position_score", [],
            {"resource_id": "scores/scoredir_two/subscore"},
            annotator_id="A0_scores/scoredir_two/subscore",
        ),
    ]


def test_wildcard_label_single(test_grr: GenomicResourceRepo) -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - position_score: score_*[foo=ALPHA]
    """, grr=test_grr)
    assert pipeline_config == [
        AnnotatorInfo(
            "position_score", [], {"resource_id": "score_one"},
            annotator_id="A0_score_one",
        ),
    ]


def test_wildcard_label_and_dir(test_grr: GenomicResourceRepo) -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - position_score: "*[foo=ALPHA]"
    """, grr=test_grr)
    assert pipeline_config == [
        AnnotatorInfo(
            "position_score", [], {"resource_id": "score_one"},
            annotator_id="A0_score_one",
        ),
        AnnotatorInfo(
            "position_score", [],
            {"resource_id": "scores/scoredir_one/subscore"},
            annotator_id="A0_scores/scoredir_one/subscore",
        ),
    ]


def test_wildcard_label_multiple(test_grr: GenomicResourceRepo) -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - position_score: "*[foo=ALPHA and bar=GAMMA]"
    """, grr=test_grr)
    assert pipeline_config == [
        AnnotatorInfo(
            "position_score", [], {"resource_id": "score_one"},
            annotator_id="A0_score_one",
        ),
    ]


def test_wildcard_label_substring(test_grr: GenomicResourceRepo) -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str("""
        - position_score: "*[baz=sub_*]"
    """, grr=test_grr)
    assert pipeline_config == [
        AnnotatorInfo(
            "position_score", [], {"resource_id": "score_one"},
            annotator_id="A0_score_one",
        ),
        AnnotatorInfo(
            "position_score", [], {"resource_id": "score_two"},
            annotator_id="A0_score_two",
        ),
    ]


def test_parse_preambule() -> None:
    preambule, _ = AnnotationConfigParser.parse_str("""
        preambule:
          summary: asdf
          description: lorem ipsum
          input_reference_genome: acgt_genome
          metadata:
              foo: bar
              subdata:
                  a: b
        annotators:
          - sample_annotator
    """)

    assert preambule == AnnotationPreambule(
        "asdf", "lorem ipsum", "acgt_genome", None,
        {"foo": "bar", "subdata": {"a": "b"}},
    )


def test_parse_preambule_with_valid_genome(
    test_grr: GenomicResourceRepo,
) -> None:
    preambule, _ = AnnotationConfigParser.parse_str("""
        preambule:
          input_reference_genome: dummy_genome
        annotators:
          - sample_annotator
    """, grr=test_grr)
    assert preambule is not None
    assert preambule.input_reference_genome == "dummy_genome"
    assert preambule.input_reference_genome_res is not None


def test_parse_preambule_no_preambule() -> None:
    preambule, _ = AnnotationConfigParser.parse_str("""
        - annotator:
            attributes:
            - att1
    """)
    assert preambule is None
