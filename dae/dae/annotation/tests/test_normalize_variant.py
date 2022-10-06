# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
import pytest

from dae.testing import convert_to_tab_separated
from dae.genomic_resources.testing import build_test_resource
from dae.genomic_resources.reference_genome import \
    build_reference_genome_from_resource
from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotation_factory import AnnotationConfigParser, \
    build_annotation_pipeline

from dae.annotation.normalize_allele_annotator import normalize_allele, \
    NormalizeAlleleAnnotator


@pytest.fixture
def example_1_genome():
    # Example from
    # https://genome.sph.umich.edu/wiki/File:Normalization_mnp.png

    res = build_test_resource({
        "genomic_resource.yaml": "{type: genome, filename: chr.fa}",
        "chr.fa": convert_to_tab_separated("""
                >1
                GGGGCATGGGG

        """),
        "chr.fa.fai": "1\t11\t3\t11\t12\n"
    })
    genome = build_reference_genome_from_resource(res)
    return genome


@pytest.mark.parametrize("beg,end,seq", [
    (1, 11, "GGGGCATGGGG"),
    (4, 7, "GCAT"),
    (5, 8, "CATG"),
    (4, 8, "GCATG"),
    (5, 7, "CAT"),
])
def test_example_1_genome_basic(example_1_genome, beg, end, seq):
    with example_1_genome.open() as genome:
        assert genome.get_chrom_length("1") == 11

        assert genome.get_sequence("1", beg, end) == seq


@pytest.fixture
def example_2_genome():
    # Example from
    # https://genome.sph.umich.edu/wiki/File:Normalization_str.png

    res = build_test_resource({
        "genomic_resource.yaml": "{type: genome, filename: chr.fa}",
        "chr.fa": convert_to_tab_separated("""
                >1
                GGGCACACACAGGG

        """),
        "chr.fa.fai": "1\t14\t3\t14\t15\n"
    })
    genome = build_reference_genome_from_resource(res)
    return genome


@pytest.mark.parametrize("beg,end,seq", [
    (1, 14, "GGGCACACACAGGG"),
    (8, 9, "CA"),
    (6, 8, "CAC"),
    (3, 7, "GCACA"),
    (2, 5, "GGCA"),
    (3, 5, "GCA"),
    (3, 3, "G"),
])
def test_example_2_genome_basic(example_2_genome, beg, end, seq):
    with example_2_genome.open() as genome:
        assert genome.get_chrom_length("1") == 14

        assert genome.get_sequence("1", beg, end) == seq


@pytest.mark.parametrize("pos,ref,alt", [
    (4, "GCAT", "GTGC"),
    (5, "CATG", "TGCG"),
    (4, "GCATG", "GTGCG"),
    (5, "CAT", "TGC"),
])
def test_example_1_normalize(example_1_genome, pos, ref, alt):
    with example_1_genome.open() as genome:
        allele = VCFAllele("1", pos, ref, alt)

        check_ref = genome.get_sequence("1", pos, pos + len(ref) - 1)
        assert ref == check_ref

        normalized = normalize_allele(allele, genome)

        assert normalized.pos == 5, (allele, normalized)
        assert normalized.ref == "CAT", (allele, normalized)
        assert normalized.alt == "TGC", (allele, normalized)


@pytest.mark.parametrize("pos,ref,alt", [
    (8, "CA", ""),
    (6, "CAC", "C"),
    (3, "GCACA", "GCA"),
    (2, "GGCA", "GG"),
    (3, "GCA", "G"),
])
def test_example_2_normalize(example_2_genome, pos, ref, alt):

    with example_2_genome.open() as genome:
        allele = VCFAllele("1", pos, ref, alt)

        check_ref = genome.get_sequence("1", pos, pos + len(ref) - 1)
        assert ref == check_ref

        normalized = normalize_allele(allele, genome)

        assert normalized.pos == 3, (allele, normalized)
        assert normalized.ref == "GCA", (allele, normalized)
        assert normalized.alt == "G", (allele, normalized)


def test_normalize_allele_annotator_config():
    pipeline_config = AnnotationConfigParser.parse(
        textwrap.dedent("""
        - normalize_allele_annotator:
            genome: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome
        """)
    )

    config = NormalizeAlleleAnnotator.validate_config(pipeline_config[0])
    assert config["annotator_type"] == "normalize_allele_annotator"

    assert config["genome"] == \
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome"


@pytest.mark.parametrize("pos,ref,alt", [
    (20_006, "TGC", "T"),  # normalized
    (20_005, "GTGC", "GT"),
    (20_006, "TGCTC", "TTC"),
    (20_004, "GGTGC", "GGT"),
    (20_007, "GC", ""),
])
def test_normalize_allele_annotator_pipeline(grr_fixture, pos, ref, alt):
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome
        """)

    annotation_pipeline = build_annotation_pipeline(
        pipeline_config_str=config, grr_repository=grr_fixture)

    with annotation_pipeline.open() as pipeline:
        assert len(pipeline.annotators) == 1
        annotator = pipeline.annotators[0]

        assert annotator.annotator_type() == "normalize_allele_annotator"
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
def test_normalize_tandem_repeats(pos, ref, alt, npos, nref, nalt):
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: hg38/genomes/GRCh38-hg38
        """)

    annotation_pipeline = build_annotation_pipeline(
        pipeline_config_str=config)

    with annotation_pipeline.open() as pipeline:
        assert pipeline is not None

        assert len(pipeline.annotators) == 1
        annotator = pipeline.annotators[0]

        assert annotator.annotator_type() == "normalize_allele_annotator"
        assert isinstance(annotator, NormalizeAlleleAnnotator)

        assert annotator.genome.get_sequence(
            "chrX", 1_948_771, 1_948_782) == "TTTTTTTTTTTT"

        allele = VCFAllele("chrX", pos, ref, alt)
        result = pipeline.annotate(allele)

        norm = result["normalized_allele"]

        assert norm.pos == npos
        assert norm.ref == nref
        assert norm.alt == nalt


def test_normalize_allele_annotator_pipeline_schema(grr_fixture):
    config = textwrap.dedent("""
        - normalize_allele_annotator:
            genome: hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome
        """)

    pipeline = build_annotation_pipeline(
        pipeline_config_str=config, grr_repository=grr_fixture)

    schema = pipeline.annotation_schema
    print(schema)

    assert "normalized_allele" in schema
    assert "normalized_allele" not in schema.public_fields
    assert "normalized_allele" in schema.internal_fields


@pytest.mark.parametrize("pos,ref,alt,npos, nref, nalt", [
    (8, "C", "C", 8, "C", "C"),
    (1, "G", "G", 1, "G", "G"),
    (1, "G", "G", 1, "G", "G"),
    (1, "GGGCA", "GGGCA", 1, "G", "G"),
    (4, "CA", "CA", 4, "C", "C"),
])
def test_normalize_novariant_allele(
        example_2_genome, pos, ref, alt, npos, nref, nalt):
    with example_2_genome.open() as genome:
        allele = VCFAllele("1", pos, ref, alt)

        check_ref = genome.get_sequence("1", pos, pos + len(ref) - 1)
        assert ref == check_ref

        normalized = normalize_allele(allele, genome)

        assert normalized.pos == npos
        assert normalized.ref == nref
        assert normalized.alt == nalt
