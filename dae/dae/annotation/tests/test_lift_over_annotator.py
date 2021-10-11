import pytest

from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.variants.variant import SummaryAllele, SummaryVariantFactory
from dae.annotation.tools.lift_over_annotator import LiftOverAnnotator


def mock_get_sequence(chrom, start, stop):
    return "G" * (stop - start + 1)


@pytest.mark.parametrize(
    "chrom,pos,lift_over,expected",
    [
        (
            "chr1",
            10000,
            lambda c, p: (c, p + 1000, "+", ""),
            "chr1:11001"
        ),
        (
            "chr1",
            10000,
            lambda c, p: (c, p + 2000, "+", ""),
            "chr1:12001",
        ),
        (
            "chr1",
            10000,
            lambda c, p: None,
            None
        ),
    ],
)
def test_lift_over(mocker, chrom, pos, lift_over, expected, genomes_db_2013):

    chain_resource = mocker.Mock()
    chain_resource.convert_coordinate = lift_over
    target_genome = mocker.Mock()
    target_genome.get_sequence = mock_get_sequence

    annotator = LiftOverAnnotator(
        chain_resource, target_genome, "liftover_test"
    )
    assert annotator is not None

    aline = {
        "chrom": chrom,
        "pos": pos,
    }
    allele = SummaryAllele(chrom, pos, "A", "T")
    liftover_variants = {}
    annotator._do_annotate(aline, allele, liftover_variants)

    lo_variant = liftover_variants.get("liftover_test")
    print(f"liftover variant: {lo_variant}")
    lo_location = lo_variant.details.cshl_location if lo_variant else None

    assert expected == lo_location


def test_pipeline_liftover(
        annotation_config, anno_grdb):

    pipeline = AnnotationPipeline.build(
        annotation_config, anno_grdb
    )
    records = [{
        "chrom": "chr1", "position": 69094,
        "reference": "G", "alternative": "A"
    }]
    variant = SummaryVariantFactory.blank_summary_variant_from_records(records)
    pipeline.annotate_summary_variant(variant)
    assert variant.get_attribute("mpc")[0] is not None
