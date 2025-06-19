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
from dae.genomic_resources.testing import (
    build_filesystem_test_repository,
    setup_genome,
)
from dae.testing.t4c8_import import GENOME_CONTENT


@pytest.fixture
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
            genome: t4c8_genome
        """),
    )

    assert pipeline_config[0].type == "normalize_allele_annotator"

    assert pipeline_config[0].parameters["genome"] == "t4c8_genome"


@pytest.mark.parametrize("pos,ref,alt", [
    (4, "GCAT", "GTGC"),
    (5, "CATG", "TGCG"),
    (4, "GCATG", "GTGCG"),
    (5, "CAT", "TGC"),
])
def test_normalize_allele_annotator_pipeline(
        t4c8_grr: GenomicResourceRepo,
        pos: int, ref: str, alt: str) -> None:
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: normalize_genome_1
            attributes:
            - source: normalized_allele
              name: normalized_allele
              internal: False
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, t4c8_grr)

    with annotation_pipeline.open() as pipeline:
        assert len(pipeline.annotators) == 1
        annotator = pipeline.annotators[0]

        assert annotator.get_info().type == "normalize_allele_annotator"
        assert isinstance(annotator, NormalizeAlleleAnnotator)

        assert annotator.genome.get_sequence("1", 1, 10) == "GGGGCATGGG"

        allele = VCFAllele("1", pos, ref, alt)
        result = pipeline.annotate(allele)

        norm = result["normalized_allele"]

        assert norm.pos == 5
        assert norm.ref == "CAT"
        assert norm.alt == "TGC"


@pytest.mark.parametrize("pos,ref,alt, npos, nref, nalt", [
    (2, "TTTTTTTTTTTT", "TTTTTTTTTTT", 1, "AT", "A"),
    (2, "TTTTTTTTTTTT", "TTTTTTTTTT", 1, "ATT", "A"),
    (2, "TTTTTTTTTTTT", "TTTTTTTTTTTTT", 1, "A", "AT"),
    (2, "TTTTTTTTTTTT", "TTTTTTTTTTTTTT", 1, "A", "ATT"),
])
def test_normalize_tandem_repeats(
    pos: int, ref: str, alt: str,
    npos: int, nref: str, nalt: str,
    t4c8_grr: GenomicResourceRepo,
) -> None:
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: tr_genome
            attributes:
            - source: normalized_allele
              name: normalized_allele
              internal: False
        """)

    grr = t4c8_grr
    annotation_pipeline = load_pipeline_from_yaml(config, grr)

    with annotation_pipeline.open() as pipeline:
        assert pipeline is not None

        assert len(pipeline.annotators) == 1
        annotator = pipeline.annotators[0]

        assert annotator.get_info().type == "normalize_allele_annotator"
        assert isinstance(annotator, NormalizeAlleleAnnotator)

        assert annotator.genome.get_sequence(
            "1", 2, 15) == "TTTTTTTTTTTTTT"

        allele = VCFAllele("1", pos, ref, alt)
        result = pipeline.annotate(allele)

        norm = result["normalized_allele"]

        assert norm.pos == npos
        assert norm.ref == nref
        assert norm.alt == nalt


def test_normalize_allele_annotator_pipeline_schema(
    t4c8_grr: GenomicResourceRepo,
) -> None:
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: tr_genome
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, t4c8_grr)

    attributes = annotation_pipeline.get_attributes()
    assert len(attributes) == 1
    assert attributes[0].name == "normalized_allele"
    assert attributes[0].internal


def test_normalize_allele_annotator_resources(
    t4c8_grr: GenomicResourceRepo,
) -> None:
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: tr_genome
            attributes:
            - source: normalized_allele
              name: normalized_allele
              internal: False
        """)

    annotation_pipeline = load_pipeline_from_yaml(config, t4c8_grr)

    with annotation_pipeline.open() as pipeline:
        annotator = pipeline.annotators[0]
        assert {res.get_id() for res in annotator.resources} == {
            "tr_genome",
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
