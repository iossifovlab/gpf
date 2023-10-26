# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest

from dae.genomic_resources.repository import GenomicResourceProtocolRepo, \
    GenomicResourceRepo
from dae.genomic_resources.testing import \
    build_inmemory_test_repository, convert_to_tab_separated
from dae.annotation.annotatable import Position
from dae.annotation.annotatable import Region
from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_factory import build_annotation_pipeline


@pytest.fixture(scope="module")
def grr() -> GenomicResourceProtocolRepo:
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
                """)  # noqa
        }
    })


@pytest.mark.parametrize("annotatable, effect, genes", [
    (Position("foo", 2), "intergenic", ""),
    (Position("foo", 7), "inter-coding_intronic", "g1"),
    (Position("foo", 14), "coding", "g1"),
    (Position("bar", 16), "peripheral", "g2"),
    (Region("bar", 14, 20), "coding", "g2"),
    (Region("bar", 16, 20), "peripheral", "g2"),
    (VCFAllele("bar", 16, "AACC", "A"), "peripheral", "g2"),
])
def test_basic(
    annotatable: Annotatable,
    effect: str,
    genes: str,
    grr: GenomicResourceRepo
) -> None:
    pipeline = build_annotation_pipeline(
        pipeline_config_str=textwrap.dedent("""
            - simple_effect_annotator:
                gene_models: gene_models
            """),
        grr_repository=grr)

    atts = pipeline.annotate(annotatable)
    assert atts["effect"] == effect
    assert atts["genes"] == genes
