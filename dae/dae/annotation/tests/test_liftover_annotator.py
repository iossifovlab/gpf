import pytest
from typing import cast

from dae.annotation.annotatable import VCFAllele

from dae.genomic_resources.reference_genome import \
    open_reference_genome_from_resource
from dae.genomic_resources.liftover_resource import \
    load_liftover_chain_from_resource

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

    chain = mocker.Mock()
    chain.convert_coordinate = lift_over
    chain.open = lambda: chain

    target_genome = mocker.Mock()
    target_genome.get_sequence = mock_get_sequence
    target_genome.open = lambda: target_genome

    config = {
        "annotator_type": "liftover_annotator",
        "chain": "test_lifover_chain",
        "target_genome": "test_target_genome",
        "id": "liftover_test",
        "attributes": None
    }

    annotator = LiftOverAnnotator(
        config, chain, target_genome)
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
        annotation_config, grr_fixture):

    pipeline = build_annotation_pipeline(
        pipeline_config_file=annotation_config, grr_repository=grr_fixture)

    allele = Allele.build_vcf_allele("chr1", 69094, "G", "A")
    attributes = pipeline.annotate(allele.get_annotatable())
    assert attributes.get("mpc") is not None


@pytest.mark.parametrize("chrom,pos,ref,alt", [
    ("1", 13199996, "C", "T"),
    ("1", 13047220, "C", "G"),
    ("1", 12892619, "C", "T"),
    ("1", 2690489, "C", "G"),
])
def test_liftover_annotator_denovo_db_examples(
        gpf_instance_2013, chrom, pos, ref, alt):

    config = {
        "annotator_type": "liftover_annotator",
        "chain": "liftover/hg19ToHg38",
        "target_genome": "hg38/genomes/GRCh38-hg38",
    }

    grr = gpf_instance_2013.grr

    target_genome_resource = grr.get_resource("hg38/genomes/GRCh38-hg38")
    assert target_genome_resource is not None
    target_genome = open_reference_genome_from_resource(target_genome_resource)
    assert target_genome is not None

    lifover_chain_resource = grr.get_resource("liftover/hg19ToHg38")
    assert lifover_chain_resource is not None
    lifover_chain = load_liftover_chain_from_resource(lifover_chain_resource)
    assert lifover_chain is not None

    liftover_annotator = LiftOverAnnotator(
        config, lifover_chain, target_genome)
    assert liftover_annotator is not None

    allele = VCFAllele(chrom, pos, ref, alt)

    result = liftover_annotator.annotate(allele, {})
    print(result)

    liftover_allele = cast(VCFAllele, result.get("liftover_annotatable"))
    assert liftover_allele is None
