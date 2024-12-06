# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pathlib
import textwrap

import pytest
import pytest_mock

from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_config import (
    AnnotationConfigParser,
)
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.annotation.normalize_allele_annotator import (
    NormalizeAlleleAnnotator,
)
from dae.genomic_resources.genomic_context import SimpleGenomicContext
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource_id,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_genome,
)
from dae.testing.t4c8_import import GENOME_CONTENT


@pytest.fixture()
def grr(tmp_path: pathlib.Path) -> GenomicResourceRepo:
    setup_genome(tmp_path / "t4c8_genome_implicit_A" / "chrAll.fa",
                 GENOME_CONTENT)
    setup_genome(tmp_path / "t4c8_genome_implicit_B" / "chrAll.fa",
                 GENOME_CONTENT)
    return build_filesystem_test_repository(tmp_path)


def test_normalize_allele_annotator_config() -> None:
    _, pipeline_config = AnnotationConfigParser.parse_str(
        textwrap.dedent("""
        - normalize_allele_annotator:
            genome: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome
        """),
    )

    assert pipeline_config[0].type == "normalize_allele_annotator"

    assert pipeline_config[0].parameters["genome"] == \
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome"


@pytest.mark.parametrize("pos,ref,alt", [
    (20_006, "TGC", "T"),  # normalized
    (20_005, "GTGC", "GT"),
    (20_006, "TGCTC", "TTC"),
    (20_004, "GGTGC", "GGT"),
    (20_007, "GC", ""),
])
def test_normalize_allele_annotator_pipeline(
        grr_fixture: GenomicResourceRepo,
        pos: int, ref: str, alt: str) -> None:
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome
            attributes:
            - source: normalized_allele
              name: normalized_allele
              internal: False
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, grr_fixture)

    with annotation_pipeline.open() as pipeline:
        assert len(pipeline.annotators) == 1
        annotator = pipeline.annotators[0]

        assert annotator.get_info().type == "normalize_allele_annotator"
        assert isinstance(annotator, NormalizeAlleleAnnotator)

        assert annotator.genome.get_sequence("1", 20_001, 20_010) ==  \
            "CCTGGTGCTC"

        allele = VCFAllele("1", pos, ref, alt)
        result = pipeline.annotate(allele)

        norm = result["normalized_allele"]

        assert norm.pos == 20_006
        assert norm.ref == "TGC"
        assert norm.alt == "T"


@pytest.mark.parametrize("pos,ref,alt, npos, nref, nalt", [
    (1_948_771, "TTTTTTTTTTTT", "TTTTTTTTTTT", 1_948_770, "AT", "A"),
    (1_948_771, "TTTTTTTTTTTT", "TTTTTTTTTT", 1_948_770, "ATT", "A"),
    (1_948_771, "TTTTTTTTTTTT", "TTTTTTTTTTTTT", 1_948_770, "A", "AT"),
    (1_948_771, "TTTTTTTTTTTT", "TTTTTTTTTTTTTT", 1_948_770, "A", "ATT"),
])
def test_normalize_tandem_repeats(
        pos: int, ref: str, alt: str,
        npos: int, nref: str, nalt: str) -> None:
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: hg38/genomes/GRCh38-hg38
            attributes:
            - source: normalized_allele
              name: normalized_allele
              internal: False
        """)

    grr = build_genomic_resource_repository()

    annotation_pipeline = load_pipeline_from_yaml(config, grr)

    with annotation_pipeline.open() as pipeline:
        assert pipeline is not None

        assert len(pipeline.annotators) == 1
        annotator = pipeline.annotators[0]

        assert annotator.get_info().type == "normalize_allele_annotator"
        assert isinstance(annotator, NormalizeAlleleAnnotator)

        assert annotator.genome.get_sequence(
            "chrX", 1_948_771, 1_948_782) == "TTTTTTTTTTTT"

        allele = VCFAllele("chrX", pos, ref, alt)
        result = pipeline.annotate(allele)

        norm = result["normalized_allele"]

        assert norm.pos == npos
        assert norm.ref == nref
        assert norm.alt == nalt


def test_normalize_allele_annotator_pipeline_schema(
        grr_fixture: GenomicResourceRepo) -> None:
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, grr_fixture)

    attributes = annotation_pipeline.get_attributes()
    assert len(attributes) == 1
    assert attributes[0].name == "normalized_allele"
    assert attributes[0].internal


def test_normalize_allele_annotator_resources(
        grr_fixture: GenomicResourceRepo) -> None:
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome
            attributes:
            - source: normalized_allele
              name: normalized_allele
              internal: False
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, grr_fixture)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]
        assert {res.get_id() for res in annotator.resources} == {
            "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome",
        }


def test_normalize_allele_annotator_implicit_genome_from_preamble(
    grr: GenomicResourceRepo,
) -> None:
    genome_id = "t4c8_genome_implicit_A"
    config = textwrap.dedent(f"""
        preamble:
          input_reference_genome: {genome_id}
        annotators:
          - normalize_allele_annotator:
              attributes:
              - source: normalized_allele
                name: normalized_allele
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, grr)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]
        assert {res.get_id() for res in annotator.resources} == {genome_id}


def test_normalize_allele_annotator_implicit_genome_from_context(
    mocker: pytest_mock.MockerFixture,
    grr: GenomicResourceRepo,
) -> None:
    genome_id = "t4c8_genome_implicit_B"
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            attributes:
            - source: normalized_allele
              name: normalized_allele
        """)

    genome = build_reference_genome_from_resource_id(genome_id, grr)
    context = SimpleGenomicContext(
        context_objects={"reference_genome": genome}, source=())
    mocker.patch(
        "dae.annotation.normalize_allele_annotator.get_genomic_context",
    ).return_value = context

    annotation_pipeline = load_pipeline_from_yaml(config, grr)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]
        assert {res.get_id() for res in annotator.resources} == {genome_id}
