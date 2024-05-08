# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from typing import Callable, cast

import pytest
from pytest_mock import MockerFixture

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import AnnotatorInfo
from dae.annotation.liftover_annotator import (
    LiftOverAnnotator,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.gpf_instance import GPFInstance
from dae.variants.core import Allele


def mock_get_sequence(_: str, start: int, stop: int) -> str:
    return "G" * (stop - start + 1)


@pytest.mark.parametrize(
    "chrom,pos,lift_over,expected_chrom,expected_pos",
    [
        (
            "chr1",
            10000,
            lambda c, p: (c, p + 1000, "+", ""),
            "chr1", 11000,
        ),
        (
            "chr1",
            10000,
            lambda c, p: (c, p + 2000, "+", ""),
            "chr1", 12000,
        ),
        (
            "chr1",
            10000,
            lambda c, p: None,
            None, None,
        ),
    ],
)
def test_liftover(
        mocker: MockerFixture,
        chrom: str, pos: int,
        lift_over: Callable[[str, int, int], tuple[str, int, str, str]],
        expected_chrom: str, expected_pos: int) -> None:

    chain = mocker.Mock()
    chain.convert_coordinate = lift_over
    chain.open = lambda: chain

    source_genome = mocker.Mock()
    source_genome.get_sequence = mock_get_sequence
    source_genome.open = lambda: source_genome

    target_genome = mocker.Mock()
    target_genome.get_sequence = mock_get_sequence
    target_genome.open = lambda: target_genome

    annotator = LiftOverAnnotator(
        None, AnnotatorInfo("gosho", [], {}),
        chain, source_genome, target_genome)
    assert annotator is not None

    allele = Allele.build_vcf_allele(chrom, pos, "A", "T")

    result = annotator._do_annotate(allele.get_annotatable(), {})
    assert isinstance(result, dict)

    lo_allele = result.get("liftover_annotatable")
    lo_chrom = lo_allele.chrom if lo_allele else None
    lo_pos = lo_allele.position if lo_allele else None

    assert expected_chrom == lo_chrom
    assert expected_pos == lo_pos


def test_pipeline_liftover(
        annotation_config: str,
        grr_fixture: GenomicResourceRepo) -> None:

    pipeline = build_annotation_pipeline(
        pipeline_config_file=annotation_config, grr_repository=grr_fixture)
    with pipeline.open() as work_pipeline:
        allele = Allele.build_vcf_allele("chr1", 69094, "G", "A")
        attributes = work_pipeline.annotate(allele.get_annotatable())
        assert attributes.get("mpc") is not None


@pytest.mark.parametrize("chrom,pos,ref,alt", [
    ("1", 13199996, "C", "T"),
    ("1", 13047220, "C", "G"),
    ("1", 12892619, "C", "T"),
    ("1", 2690489, "C", "G"),
])
def test_liftover_annotator_denovo_db_examples(
        gpf_instance_2013: GPFInstance,
        chrom: str, pos: int, ref: str, alt: str) -> None:

    pipeline_config = textwrap.dedent("""
        - liftover_annotator:
            chain: liftover/hg19ToHg38
            source_genome: hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174
            target_genome: hg38/genomes/GRCh38-hg38
        """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=gpf_instance_2013.grr)

    allele = VCFAllele(chrom, pos, ref, alt)

    result = pipeline.annotate(allele)

    liftover_allele = cast(VCFAllele, result.get("liftover_annotatable"))
    assert liftover_allele is None


def test_liftover_annotator_resources(
        grr_fixture: GenomicResourceRepo) -> None:

    pipeline_config = textwrap.dedent("""
      - liftover_annotator:
          chain: hg38/hg38tohg19
          source_genome: hg38/GRCh38-hg38/genome
          target_genome: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome
      """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=pipeline_config,
        grr_repository=grr_fixture)

    assert pipeline.get_resource_ids() == {
        "hg38/hg38tohg19",
        "hg38/GRCh38-hg38/genome",
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome",
    }
