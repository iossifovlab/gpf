import textwrap
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import \
    build_inmemory_test_repository, convert_to_tab_separated
from dae.annotation.annotatable import Position
from dae.annotation.annotatable import Region
from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import build_annotation_pipeline
import pytest


@pytest.fixture(scope="module")
def grr():
    return build_inmemory_test_repository({
        "gene_models": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: gene_models
                filename: gene_models.tsv
                format: "refflat"
            """),

            "gene_models.tsv": convert_to_tab_separated("""
                #geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds 
                g1        tx1  foo   +      3       17    3        17     2         3,13       6,17
                g1        tx2  foo   +      3       9     3        6      1         3          6
                g2        tx3  bar   -      3       20    3        15     1         3          17
                """  # noqa
            )
        }
    })


def test_basic(grr: GenomicResourceRepo):
    pipeline = build_annotation_pipeline(
        pipeline_config_str=textwrap.dedent("""
            - simple_effect_annotator:
                gene_models: gene_models
            """),
        grr_repository=grr)

    atts = pipeline.annotate(Position("foo", 2))
    assert atts["effect"] == "intergenic"
    assert atts["genes"] == ""

    atts = pipeline.annotate(Position("foo", 7))
    assert atts["effect"] == "inter-coding_intronic"
    assert atts["genes"] == "g1"

    atts = pipeline.annotate(Position("foo", 14))
    assert atts["effect"] == "coding"
    assert atts["genes"] == "g1"

    atts = pipeline.annotate(Position("bar", 16))
    assert atts["effect"] == "peripheral"
    assert atts["genes"] == "g2"

    atts = pipeline.annotate(Region("bar", 14, 20))
    assert atts["effect"] == "coding"
    assert atts["genes"] == "g2"

    atts = pipeline.annotate(Region("bar", 16, 20))
    assert atts["effect"] == "peripheral"
    assert atts["genes"] == "g2"

    atts = pipeline.annotate(VCFAllele("bar", 16, "AACC", "A"))
    assert atts["effect"] == "peripheral"
    assert atts["genes"] == "g2"
