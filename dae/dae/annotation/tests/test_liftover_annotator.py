import pytest
from box import Box

from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.variants.core import Allele
from dae.annotation.liftover_annotator import LiftOverAnnotator


def mock_get_sequence(chrom, start, stop):
    return "G" * (stop - start + 1)


@pytest.mark.parametrize(
    "chrom,pos,lift_over,expected_chrom,expected_pos",
    [
        (
            "chr1",
            10000,
            lambda c, p: (c, p + 1000, "+", ""),
            "chr1", 11001
        ),
        (
            "chr1",
            10000,
            lambda c, p: (c, p + 2000, "+", ""),
            "chr1", 12001,
        ),
        (
            "chr1",
            10000,
            lambda c, p: None,
            None, None
        ),
    ],
)
def test_liftover(
        mocker, chrom, pos, lift_over, expected_chrom, expected_pos):

    chain_resource = mocker.Mock()
    chain_resource.convert_coordinate = lift_over
    target_genome = mocker.Mock()
    target_genome.get_sequence = mock_get_sequence

    config = Box({
        "annotator_type": "liftover_annotator",
        "chain": "test_lifover_chain",
        "target_genome": "test_target_genome",
        "id": "liftover_test",
        "attributes": None
    })

    annotator = LiftOverAnnotator(
        config, chain_resource, target_genome)
    assert annotator is not None

    # aline = {
    #     "chrom": chrom,
    #     "pos": pos,
    # }

    allele = Allele.build_vcf_allele(chrom, pos, "A", "T")
    context = {}
    result = annotator._do_annotate(allele.get_annotatable(), context)
    assert isinstance(result, dict)

    lo_allele = result.get("liftover_annotatable")
    print(f"liftover allele: {lo_allele}", context)
    lo_chrom = lo_allele.chrom if lo_allele else None
    lo_pos = lo_allele.position if lo_allele else None

    assert expected_chrom == lo_chrom
    assert expected_pos == lo_pos


def test_pipeline_liftover(
        annotation_config, anno_grdb):

    pipeline = build_annotation_pipeline(
        pipeline_config_file=annotation_config, grr_repository=anno_grdb
    )
    allele = Allele.build_vcf_allele("chr1", 69094, "G", "A")
    attributes = pipeline.annotate(allele.get_annotatable())
    assert attributes.get("mpc") is not None
