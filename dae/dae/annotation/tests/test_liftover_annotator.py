# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
from typing import cast

import pytest

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import (
    load_pipeline_from_file,
    load_pipeline_from_yaml,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_directories,
)
from dae.gpf_instance import GPFInstance
from dae.variants.core import Allele


@pytest.fixture
def dummy_liftover_grr_fixture(
    tmp_path_factory: pytest.TempPathFactory,
) -> GenomicResourceRepo:
    root_path = tmp_path_factory.mktemp("dummy_liftover_grr_fixture")
    setup_directories(root_path, {
        "genomeA": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "genomeB": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: genome
                filename: genome.fa
            """),
        },
        "dummyChain": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: liftover_chain
                filename: liftover.chain.gz
                meta:
                  labels:
                    source_genome: genomeA
                    target_genome: genomeB
            """),
        },
    })
    return build_filesystem_test_repository(root_path)


def test_pipeline_liftover(
        annotation_config: str,
        grr_fixture: GenomicResourceRepo) -> None:

    pipeline = load_pipeline_from_file(annotation_config, grr_fixture)
    with pipeline.open() as work_pipeline:
        allele = Allele.build_vcf_allele("chr1", 69094, "G", "A")
        attributes = work_pipeline.annotate(allele.get_annotatable())
        assert attributes.get("mpc") is not None


@pytest.mark.parametrize("chrom,pos,ref,alt,expected", [
    ("1", 13199996, "C", "T", VCFAllele("chr1", 13132543, "T", "C")),
    ("1", 13047220, "C", "G", None),
    ("1", 12892619, "C", "T", VCFAllele("chr1", 12832765, "T", "C")),
    ("1", 2690489, "C", "G", VCFAllele("chr1", 2773943, "G", "C")),
])
def test_liftover_annotator_denovo_db_examples(
    gpf_instance_2013: GPFInstance,
    chrom: str, pos: int, ref: str, alt: str,
    expected: VCFAllele | None,
) -> None:

    pipeline_config = textwrap.dedent("""
        - liftover_annotator:
            chain: liftover/hg19ToHg38
            source_genome: hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174
            target_genome: hg38/genomes/GRCh38-hg38
        """)

    pipeline = load_pipeline_from_yaml(pipeline_config, gpf_instance_2013.grr)

    allele = VCFAllele(chrom, pos, ref, alt)

    result = pipeline.annotate(allele)

    liftover_allele = cast(VCFAllele, result.get("liftover_annotatable"))
    assert liftover_allele == expected


def test_liftover_annotator_resources(
        grr_fixture: GenomicResourceRepo) -> None:

    pipeline_config = textwrap.dedent("""
      - liftover_annotator:
          chain: hg38/hg38tohg19
          source_genome: hg38/GRCh38-hg38/genome
          target_genome: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome
      """)

    pipeline = load_pipeline_from_yaml(pipeline_config, grr_fixture)

    assert pipeline.get_resource_ids() == {
        "hg38/hg38tohg19",
        "hg38/GRCh38-hg38/genome",
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome",
    }


def test_liftover_annotator_implicit_genomes(
    dummy_liftover_grr_fixture: GenomicResourceRepo,
) -> None:
    pipeline_config = textwrap.dedent("""
      - liftover_annotator:
          chain: dummyChain
      """)
    pipeline = load_pipeline_from_yaml(
        pipeline_config, dummy_liftover_grr_fixture)
    assert pipeline.get_resource_ids() == {
        "genomeA",
        "genomeB",
        "dummyChain",
    }
