# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.annotation.annotation_pipeline import AnnotatorInfo, AttributeInfo
from dae.annotation.annotation_factory import AnnotationConfigParser


def test_simple_annotator_simple() -> None:
    pipeline_config = AnnotationConfigParser.parse_str("""
        - annotator:
            resource_id: resource
    """)

    assert pipeline_config == \
        [AnnotatorInfo("annotator", [], {"resource_id": "resource"})]


def test_short_annotator_config() -> None:
    pipeline_config = AnnotationConfigParser.parse_str("""
        - annotator: resource
    """)

    assert pipeline_config == \
        [AnnotatorInfo("annotator", [], {"resource_id": "resource"})]


def test_minimal_annotator_config() -> None:
    pipeline_config = AnnotationConfigParser.parse_str("""
        - annotator
    """)
    assert pipeline_config == [AnnotatorInfo("annotator", [], {})]


def test_annotator_config_with_more_parameters() -> None:
    pipeline_config = AnnotationConfigParser.parse_str("""
        - annotator:
                resource_id: resource
                key: value
    """)

    assert pipeline_config == \
        [AnnotatorInfo("annotator", [], {"resource_id": "resource",
                                         "key": "value"})]


def test_annotator_config_with_attributes() -> None:
    pipeline_config = AnnotationConfigParser.parse_str("""
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
            {})]


def test_annotator_config_with_params_and_attributes() -> None:
    pipeline_config = AnnotationConfigParser.parse_str("""
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
            "resource_id": "resource"
        })]


def test_empty_config() -> None:
    pipeline_config = AnnotationConfigParser.parse_str("")

    # pylint: disable=use-implicit-booleaness-not-comparison
    assert pipeline_config == []


def test_effect_annotator_extra_attributes() -> None:
    pipeline_config = AnnotationConfigParser.parse_str("""
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
            "promoter_len": 100}
        )
    ]
