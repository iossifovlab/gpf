import pytest
import textwrap

from dae.annotation.annotation_pipeline import AnnotationConfigParser


def test_np_score_annotator_simple():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - np_score:
                resource_id: np_score1
            """)
    )
    assert pipeline_config is not None

    assert isinstance(pipeline_config, list)
    assert len(pipeline_config) == 1

    config = pipeline_config[0]
    print(config)
    assert "annotator_type" in config
    assert config["annotator_type"] == "np_score"
    assert config.annotator_type == "np_score"

    assert config["resource_id"] == "np_score1"
    assert config.resource_id == "np_score1"

    assert "position_score" not in config
    assert config.get("position_score") is None


def test_np_score_annotator_short():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - np_score: np_score1
            """)
    )
    assert pipeline_config is not None
    assert isinstance(pipeline_config, list)
    assert len(pipeline_config) == 1

    config = pipeline_config[0]
    print(config)
    assert config.annotator_type == "np_score"
    assert config["resource_id"] == "np_score1"
    assert config.resource_id == "np_score1"


def test_np_score_annotator_with_liftover():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - np_score:
                resource_id: np_score1
                liftover_id: hg38tohg19
            """)
    )
    assert pipeline_config is not None
    assert isinstance(pipeline_config, list)
    assert len(pipeline_config) == 1

    config = pipeline_config[0]
    print(config)
    assert config.annotator_type == "np_score"
    assert config.resource_id == "np_score1"
    assert config.liftover_id == "hg38tohg19"


def test_np_score_annotator_without_liftover():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - np_score:
                resource_id: np_score1
            """)
    )
    assert pipeline_config is not None
    assert isinstance(pipeline_config, list)
    assert len(pipeline_config) == 1

    config = pipeline_config[0]
    print(config)
    assert config.annotator_type == "np_score"
    assert config.resource_id == "np_score1"
    assert config.liftover_id is None


def test_np_score_annotator_attributes():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - np_score:
                resource_id: hg38/TESTCADD
                attributes:
                - destination: score1
                  source: score1
                - destination: score2
                  source: score2
                - destination: score3
                  source: score3
            """)
    )
    assert pipeline_config is not None
    assert isinstance(pipeline_config, list)
    assert len(pipeline_config) == 1

    config = pipeline_config[0]
    print(config)
    assert config["annotator_type"] == "np_score"
    assert config.annotator_type == "np_score"

    assert config["resource_id"] == "hg38/TESTCADD"
    assert config.resource_id == "hg38/TESTCADD"

    assert len(config["attributes"]) == 3
    attributes = config.attributes
    assert len(attributes) == 3

    assert attributes[0].source == "score1"
    assert attributes[0].destination == "score1"

    assert attributes[1].source == "score2"
    assert attributes[1].destination == "score2"

    assert attributes[2].source == "score3"
    assert attributes[2].destination == "score3"


def test_np_score_annotator_attributes_short():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - np_score:
                resource_id: hg38/TESTCADD
                attributes:
                - score1
                - score2
                - score3
            """)
    )

    config = pipeline_config[0]
    print(config)
    assert config["annotator_type"] == "np_score"
    assert config.annotator_type == "np_score"

    assert config["resource_id"] == "hg38/TESTCADD"
    assert config.resource_id == "hg38/TESTCADD"

    assert len(config["attributes"]) == 3
    attributes = config.attributes
    assert len(attributes) == 3

    assert attributes[0].source == "score1"
    assert attributes[0].destination == "score1"

    assert attributes[1].source == "score2"
    assert attributes[1].destination == "score2"

    assert attributes[2].source == "score3"
    assert attributes[2].destination == "score3"


def test_np_score_annotator_attributes_sources_only():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - np_score:
                resource_id: hg38/TESTCADD
                attributes:
                - source: score1
                - source: score2
                - source: score3
            """)
    )
    assert pipeline_config is not None
    assert isinstance(pipeline_config, list)
    assert len(pipeline_config) == 1

    config = pipeline_config[0]
    attributes = config.attributes
    assert len(attributes) == 3

    assert attributes[0].source == "score1"
    assert attributes[0].destination == "score1"

    assert attributes[1].source == "score2"
    assert attributes[1].destination == "score2"

    assert attributes[2].source == "score3"
    assert attributes[2].destination == "score3"


def test_np_score_annotator_attributes_with_aggr():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
        - np_score:
            resource_id: hg38/TESTCADD
            attributes:
            - destination: score1
              source: score1
              position_aggregator: mean
              nucleotide_aggregator: mean
            """)
    )
    assert pipeline_config is not None
    assert isinstance(pipeline_config, list)
    assert len(pipeline_config) == 1

    config = pipeline_config[0]

    attributes = config.attributes
    assert len(attributes) == 1

    assert attributes[0].source == "score1"
    assert attributes[0].destination == "score1"
    assert attributes[0].position_aggregator == "mean"
    assert attributes[0].nucleotide_aggregator == "mean"


def test_np_score_annotator_attributes_without_aggr():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
        - np_score:
            resource_id: hg38/TESTCADD
            attributes:
            - destination: score1
              source: score1
            """)
    )
    config = pipeline_config[0]

    attributes = config.attributes
    assert len(attributes) == 1

    assert attributes[0].source == "score1"
    assert attributes[0].destination == "score1"
    assert "position_aggregator" not in attributes[0]
    assert "nucleotide_aggregator" not in attributes[0]


def test_position_score_annotator_attributes_with_aggr_fails():
    with pytest.raises(ValueError) as ex_info:
        AnnotationConfigParser.parse(
            textwrap.dedent("""
                - position_score:
                    resource_id: hg38/TESTCADD
                    attributes:
                    - destination: score1
                      source: score1
                      position_aggregator: mean
                      nucleotide_aggregator: mean
            """)
        )

    assert "nucleotide_aggregator" in str(ex_info.value)


def test_position_score_annotator_attributes_with_aggr():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
        - position_score:
            resource_id: hg38/TESTCADD
            attributes:
            - destination: score1
              source: score1
              position_aggregator: mean
            """)
    )

    config = pipeline_config[0]
    assert config.annotator_type == "position_score"

    attributes = config.attributes
    assert len(attributes) == 1

    assert attributes[0].source == "score1"
    assert attributes[0].destination == "score1"
    assert attributes[0].position_aggregator == "mean"


def test_allele_score_annotator_attributes_with_aggr_fails():
    with pytest.raises(ValueError) as ex_info:
        AnnotationConfigParser.parse(
            textwrap.dedent("""
            - allele_score:
                resource_id: hg38/TESTCADD
                attributes:
                - destination: score1
                source: score1
                position_aggregator: mean
                nucleotide_aggregator: mean
                """)
        )

    assert "nucleotide_aggregator" in str(ex_info.value)
    assert "position_aggregator" in str(ex_info.value)


def test_allele_score_annotator_attributes():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
        - allele_score:
            resource_id: hg38/TESTCADD
            attributes:
            - destination: score1
              source: score1
            """)
    )

    config = pipeline_config[0]
    assert config.annotator_type == "allele_score"

    attributes = config.attributes
    assert len(attributes) == 1

    assert attributes[0].source == "score1"
    assert attributes[0].destination == "score1"


def test_allele_score_annotator_attributes_short():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
        - allele_score:
            resource_id: hg38/TESTCADD
            attributes:
            - score1
            - score2
        """)
    )

    config = pipeline_config[0]
    assert config.annotator_type == "allele_score"
    attributes = config.attributes
    assert len(attributes) == 2

    assert attributes[0].source == "score1"
    assert attributes[0].destination == "score1"

    assert attributes[1].source == "score2"
    assert attributes[1].destination == "score2"


def test_allele_score_annotator_short_attributes_none():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
        - allele_score: hg38/TESTCADD
        """)
    )

    config = pipeline_config[0]
    assert config.annotator_type == "allele_score"
    assert config.attributes is None


def test_allele_score_annotator_no_attributes():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
        - allele_score:
            resource_id: hg38/TESTCADD
        """)
    )

    config = pipeline_config[0]
    assert config.attributes is None


def test_effect_annotator():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
        - effect_annotator:
            gene_models: hg38/GRCh38-hg38/gene_models/refSeq_20200330
            genome: hg38/GRCh38-hg38/genome
            attributes:
            - source: worst_effect
              destination: old_worst_effect
        """)
    )

    config = pipeline_config[0]
    assert config.annotator_type == "effect_annotator"

    assert config.genome == "hg38/GRCh38-hg38/genome"
    assert config.gene_models == "hg38/GRCh38-hg38/gene_models/refSeq_20200330"

    attributes = config.attributes
    assert len(attributes) == 1

    assert attributes[0].source == "worst_effect"
    assert attributes[0].destination == "old_worst_effect"


def test_effect_annotator_extra():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
        - effect_annotator:
            gene_models: hg38/GRCh38-hg38/gene_models/refSeq_20200330
            genome: hg38/GRCh38-hg38/genome
            promoter_len: 100
        """)
    )

    config = pipeline_config[0]
    assert config.annotator_type == "effect_annotator"

    assert config.promoter_len == 100


def test_effect_annotator_minimal():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
        - effect_annotator
        """)
    )

    config = pipeline_config[0]
    assert config.annotator_type == "effect_annotator"

    assert config.gene_models is None
    assert config.genome is None
    assert config.attributes is None


def test_liftover_annotator():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
            - liftover_annotator:
                resource_id: hg38/hg38tohg19
                liftover_id: hg38tohg19
                target_genome: hg19/GATK_ResourceBundle_5777_b37_phiX174/genome
        """)
    )

    config = pipeline_config[0]
    assert config.annotator_type == "liftover_annotator"

    assert config.resource_id == "hg38/hg38tohg19"
    assert config.liftover_id == "hg38tohg19"
    assert config.target_genome == \
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/genome"
