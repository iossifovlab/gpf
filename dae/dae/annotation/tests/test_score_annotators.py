import yaml
import pytest

from box import Box

from dae.annotation.tools.score_annotator import PositionScoreAnnotator
from dae.annotation.annotation_pipeline import AnnotationPipeline

from dae.variants.variant import SummaryVariantFactory
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.score_resources import PositionScoreResource


#  hg19
#  chrom: 1
#  pos:   14970
#
#  C    C    T    T    G    C    G
#  70   71   72   73   74   75   76
#  0.1  0.1  0.2  0.2  0.3  0.3  0.4
#
@pytest.mark.parametrize("variant,pos_aggregator, expected", [
    ({"reference": "C", "alternative": "A"}, "mean", 0.1),
    ({"reference": "CC", "alternative": "C"}, "mean", 0.13),
    ({"reference": "CC", "alternative": "C"}, "max", 0.2),
    ({"reference": "CCT", "alternative": "C"}, "mean", 0.15),
    ({"reference": "CCT", "alternative": "C"}, "max", 0.2),
    ({"reference": "C", "alternative": "CA"}, "mean", 0.1),
    ({"reference": "C", "alternative": "CAA"}, "mean", 0.1),
    ({"reference": "C", "alternative": "CAA"}, "max", 0.1),
])
def test_position_score_annotator(variant, pos_aggregator, expected):

    variant.update({"chrom": "1", "position": 14970})

    sv = SummaryVariantFactory.summary_variant_from_records([variant])
    assert sv is not None

    repo = build_genomic_resource_repository({
        "id": "test_annotation",
        "type": "embeded",
        "content": {
            "position_score1": {
                "genomic_resource.yaml":
                """\
                type: PositionScore
                table:
                    filename: data.mem
                scores:
                - id: test100way
                  type: float
                  desc: "test values"
                  name: 100way
                """,
                "data.mem": """
                    chrom  pos_begin  pos_end  100way
                    1      14970      14971    0.1
                    1      14972      14973    0.2
                    1      14974      14975    0.3
                    1      14976      14977    0.4
                """
            }
        }
    })
    assert len(list(repo.get_all_resources())) == 1

    resource = repo.get_resource("position_score1")
    assert resource is not None
    assert isinstance(resource, PositionScoreResource)

    annotation_override = Box({"attributes": [
            {
                "source": "test100way",
                "dest": "test100",
                "position_aggregator": pos_aggregator,
            }
        ]
    })
    annotator = PositionScoreAnnotator(resource, override=annotation_override)
    assert annotator is not None
    pipeline = AnnotationPipeline(None, None)
    pipeline.add_annotator(annotator)

    pipeline.annotate_summary_variant(sv)
    print(sv, sv.get_attribute("test100"))

    assert sv.get_attribute("test100")[0] == pytest.approx(expected, abs=1e-2)


    # annotation_config = Box(yaml.safe_load("""
    # score_annotators:
    # - annotator: position_score
    #   resource: position_score1
    #   override:
    #     attributes:
    #     - source: test100way
    #       dest: test100
    #       position_aggregator: mean
    # """))

    # print(annotation_config)
