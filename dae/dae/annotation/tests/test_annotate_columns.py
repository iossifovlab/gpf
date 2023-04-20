# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest

from dae.annotation.annotate_columns import build_record_to_annotatable
from dae.annotation.annotatable import Position, VCFAllele, Region, CNVAllele
from dae.testing import setup_directories, setup_denovo
from dae.annotation.annotate_columns import cli as cli_columns
from dae.genomic_resources.genomic_context import SimpleGenomicContext
from dae.testing import setup_genome


@pytest.mark.parametrize(
    "record,expected", [
        ({"chrom": "chr1", "pos": "3"},
         Position("chr1", 3)),

        ({"chrom": "chr1", "pos": "4", "ref": "C", "alt": "CT"},
         VCFAllele("chr1", 4, "C", "CT")),

        ({"vcf_like": "chr1:4:C:CT"},
         VCFAllele("chr1", 4, "C", "CT")),

        ({"chrom": "chr1", "pos_beg": "4", "pos_end": "30"},
         Region("chr1", 4, 30)),

        ({"chrom": "chr1", "pos_beg": "4", "pos_end": "30"},
         Region("chr1", 4, 30)),
    ]
)
def test_default_columns(record, expected):
    annotatable = build_record_to_annotatable(
        {}, set(record.keys())).build(record)
    assert str(annotatable) == str(expected)


@pytest.mark.parametrize(
    "record,expected", [
        ({"location": "chr1:13", "variant": "sub(A->T)"},
         VCFAllele("chr1", 13, "A", "T")),

        ({"location": "chr1:3-13", "variant": "duplication"},
         CNVAllele("chr1", 3, 13, CNVAllele.Type.LARGE_DUPLICATION)),
    ]
)
def test_cshl_variants_without_context(record, expected):
    with pytest.raises(ValueError):
        build_record_to_annotatable(
            {}, set(record.keys())).build(record)


@pytest.fixture
def gc_fixture(tmp_path):
    genome = setup_genome(
        tmp_path / "acgt_gpf" / "genome" / "allChr.fa",
        f"""
        >chr1
        {25 * "ACGT"}
        >chr2
        {25 * "ACGT"}
        >chr3
        {25 * "ACGT"}
        """
    )
    return SimpleGenomicContext(
        {"reference_genome": genome}, ("test", "gc_fixture"))


@pytest.mark.parametrize(
    "record,expected", [
        ({"chrom": "chr1", "pos": "3"},
         Position("chr1", 3)),

        ({"chrom": "chr1", "pos": "4", "ref": "C", "alt": "CT"},
         VCFAllele("chr1", 4, "C", "CT")),

        ({"vcf_like": "chr1:4:C:CT"},
         VCFAllele("chr1", 4, "C", "CT")),

        ({"chrom": "chr1", "pos_beg": "4", "pos_end": "30"},
         Region("chr1", 4, 30)),

        ({"chrom": "chr1", "pos_beg": "4", "pos_end": "30"},
         Region("chr1", 4, 30)),

        ({"location": "chr1:13", "variant": "sub(A->T)"},
         VCFAllele("chr1", 13, "A", "T")),

        ({"location": "chr1:14", "variant": "ins(A)"},
         VCFAllele("chr1", 13, "A", "AA")),

        ({"location": "chr1:13", "variant": "del(1)"},
         VCFAllele("chr1", 12, "TA", "T")),

        ({"location": "chr1:3-13", "variant": "duplication"},
         CNVAllele("chr1", 3, 13, CNVAllele.Type.LARGE_DUPLICATION)),

        ({"location": "chr1:3-13", "variant": "CNV+"},
         CNVAllele("chr1", 3, 13, CNVAllele.Type.LARGE_DUPLICATION)),

        ({"location": "chr1:3-13", "variant": "deletion"},
         CNVAllele("chr1", 3, 13, CNVAllele.Type.LARGE_DELETION)),

        ({"location": "chr1:3-13", "variant": "CNV-"},
         CNVAllele("chr1", 3, 13, CNVAllele.Type.LARGE_DELETION)),
    ]
)
def test_build_record(record, expected, gc_fixture):
    annotatable = build_record_to_annotatable(
        {}, set(record.keys()), gc_fixture).build(record)
    assert str(annotatable) == str(expected)


@pytest.mark.parametrize(
    "parameters,record,expected", [

        ({"col_chrom": "chromosome", "col_pos": "position"},
         {"chromosome": "chr1", "position": "4", "ref": "C", "alt": "CT"},
         VCFAllele("chr1", 4, "C", "CT")),
    ]
)
def test_renamed_columns(parameters, record, expected):
    annotatable = build_record_to_annotatable(
        parameters, set(record.keys())).build(record)
    assert str(annotatable) == str(expected)


def test_build_record_to_annotable_failures():
    with pytest.raises(
            ValueError, match="no record to annotatable could be found"):
        build_record_to_annotatable({}, set([]))

    with pytest.raises(
            ValueError, match="no record to annotatable could be found"):
        build_record_to_annotatable({"gosho": "pesho"}, set([]))


def get_file_content_as_string(file):
    with open(file, "rt", encoding="utf8") as infile:
        return "".join(infile.readlines())


@pytest.fixture
def annotate_directory_fixture(tmp_path):
    setup_directories(
        tmp_path,
        {
            "annotation.yaml": """
                - position_score: one
            """,
            "annotation_multiallelic.yaml": """
                - allele_score: two
            """,
            "grr.yaml": f"""
                id: mm
                type: dir
                directory: "{tmp_path}/grr"
            """,
            "grr": {
                "one": {
                    "genomic_resource.yaml": """
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score
                          type: float
                          desc: |
                                The phastCons computed over the tree of 100
                                verterbarte species
                          name: s1
                    """
                },
                "two": {
                    "genomic_resource.yaml": """
                        type: allele_score
                        table:
                            filename: data.txt
                            reference:
                              name: reference
                            alternative:
                              name: alternative
                        scores:
                        - id: score
                          type: float
                          name: s1
                    """
                }
            }
        }
    )
    one_content = textwrap.dedent("""
        chrom  pos_begin  s1
        chr1   23         0.1
        chr1   24         0.2
        chr2   33         0.3
        chr2   34         0.4
        chr3   43         0.5
        chr3   44         0.6
    """)
    two_content = textwrap.dedent("""
        chrom  pos_begin  reference  alternative  s1
        chr1   23         C          T            0.1
        chr1   23         C          A            0.2
        chr1   24         C          A            0.3
        chr1   24         C          G            0.4
    """)
    setup_denovo(tmp_path / "grr" / "one" / "data.txt", one_content)
    setup_denovo(tmp_path / "grr" / "two" / "data.txt", two_content)


def test_basic_setup(tmp_path, annotate_directory_fixture):
    in_content = textwrap.dedent("""
        chrom   pos
        chr1    23
        chr1    24
    """)
    out_expected_content = (
        "chrom\tpos\tscore\n"
        "chr1\t23\t0.1\n"
        "chr1\t24\t0.2\n"
    )

    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    annotation_file = tmp_path / "annotation.yaml"
    grr_file = tmp_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, out_file, "--grr", grr_file
        ]
    ])
    out_file_content = get_file_content_as_string(out_file)
    print(out_file_content)
    assert out_file_content == out_expected_content
