# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import textwrap
import gzip

import pytest
import pysam

from dae.annotation.annotate_columns import build_record_to_annotatable
from dae.annotation.annotatable import Position, VCFAllele, Region
from dae.testing import setup_directories, setup_vcf, setup_denovo
from dae.annotation.annotate_columns import cli as cli_columns
from dae.annotation.annotate_vcf import cli as cli_vcf, produce_partfile_paths


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
    ]
)
def test_default_columns(record, expected):
    annotatable = build_record_to_annotatable(
        {}, set(record.keys())).build(record)
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
            "annotation_forbidden_symbols.yaml": """
                - allele_score: three
            """,
            "annotation_quotes_in_description.yaml": """
                - position_score: four
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
                                verterbrate species
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
                },
                "three": {
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
                          type: str
                          name: s1
                    """
                },
                "four": {
                    "genomic_resource.yaml": """
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score
                          type: float
                          desc: |
                                The "phastCons" computed over the tree of 100
                                verterbrate species
                          name: s1
                    """
                },
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
        chr1   25         C          G            0.4
    """)
    three_content = textwrap.dedent("""
        chrom  pos_begin  reference  alternative  s1
        chr1   23         C          A            a;b
        chr1   24         C          A            c,d
        chr1   25         C          A            e||f
    """)
    setup_denovo(tmp_path / "grr" / "one" / "data.txt", one_content)
    setup_denovo(tmp_path / "grr" / "two" / "data.txt", two_content)
    setup_denovo(tmp_path / "grr" / "three" / "data.txt", three_content)
    setup_denovo(tmp_path / "grr" / "four" / "data.txt", one_content)


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
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
        ]
    ])
    out_file_content = get_file_content_as_string(out_file)
    assert out_file_content == out_expected_content


def test_basic_vcf(tmp_path, annotate_directory_fixture):
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)

    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    workdir = tmp_path / "output"
    annotation_file = tmp_path / "annotation.yaml"
    grr_file = tmp_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file, annotation_file, "-w", workdir, "--grr", grr_file,
            "-o", out_file
        ]
    ])

    result = []
    # pylint: disable=no-member
    with pysam.VariantFile(out_file) as vcf_file:
        for vcf in vcf_file.fetch():
            result.append(vcf.info["score"][0])
    assert result == ["0.1", "0.2"]


def test_multiallelic_vcf(tmp_path, annotate_directory_fixture):
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO
        chr1   23  .  C   T,A   .    .      .
        chr1   24  .  C   A,G   .    .      .
    """)

    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    workdir = tmp_path / "output"
    annotation_file = tmp_path / "annotation_multiallelic.yaml"
    grr_file = tmp_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file, annotation_file, "-w", workdir, "--grr", grr_file,
            "-o", out_file
        ]
    ])

    result = []
    # pylint: disable=no-member
    with pysam.VariantFile(out_file) as vcf_file:
        for vcf in vcf_file.fetch():
            result.append(vcf.info["score"])
    assert result == [("0.1", "0.2"), ("0.3", "0.4")]


def test_vcf_multiple_chroms(tmp_path, annotate_directory_fixture):
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        ##contig=<ID=chr2>
        ##contig=<ID=chr3>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr2   33  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr2   34  .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr3   43  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr3   44  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)

    in_file = tmp_path / "in.vcf.gz"
    out_file = tmp_path / "out.vcf.gz"
    out_file_tbi = tmp_path / "out.vcf.gz.tbi"
    workdir = tmp_path / "output"
    annotation_file = tmp_path / "annotation.yaml"
    grr_file = tmp_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file, annotation_file, "-w", workdir, "--grr", grr_file,
            "-o", out_file, "-j 1"
        ]
    ])

    result = []
    # pylint: disable=no-member
    with pysam.VariantFile(out_file) as vcf_file:
        for vcf in vcf_file.fetch():
            result.append(vcf.info["score"][0])
    assert result == ["0.1", "0.2",
                      "0.3", "0.4",
                      "0.5", "0.6"]
    assert os.path.exists(out_file_tbi)
    assert os.listdir(workdir) == [
        "tasks-status",  # default task status dir
        # part files must be cleaned up
    ]


def test_produce_partfile_paths():
    regions = [("chr1", 0, 1000), ("chr1", 1000, 2000), ("chr1", 2000, 3000)]
    expected_output = [
        "work_dir/output/input.vcf_annotation_chr1_0_1000.gz",
        "work_dir/output/input.vcf_annotation_chr1_1000_2000.gz",
        "work_dir/output/input.vcf_annotation_chr1_2000_3000.gz",
    ]
    # relative input file path
    assert produce_partfile_paths(
        "src/input.vcf", regions, "work_dir/output"
    ) == expected_output
    # absolute input file path
    assert produce_partfile_paths(
        "/home/user/src/input.vcf", regions, "work_dir/output"
    ) == expected_output


def test_annotate_columns_multiple_chrom(tmp_path, annotate_directory_fixture):
    in_content = textwrap.dedent("""
        chrom   pos
        chr1    23
        chr1    24
        chr2    33
        chr2    34
        chr3    43
        chr3    44
    """)
    out_expected_content = (
        "chrom\tpos\tscore\n"
        "chr1\t23\t0.1\n"
        "chr1\t24\t0.2\n"
        "chr2\t33\t0.3\n"
        "chr2\t34\t0.4\n"
        "chr3\t43\t0.5\n"
        "chr3\t44\t0.6\n"
    )

    in_file = tmp_path / "in.txt"
    in_file_gz = in_file.with_suffix(".txt.gz")
    out_file = tmp_path / "out.txt"
    out_file_tbi = tmp_path / "out.txt.gz.tbi"
    workdir = tmp_path / "output"
    annotation_file = tmp_path / "annotation.yaml"
    grr_file = tmp_path / "grr.yaml"

    setup_denovo(in_file, in_content)
    pysam.tabix_compress(str(in_file), str(in_file_gz), force=True)
    pysam.tabix_index(str(in_file_gz), force=True, line_skip=1, seq_col=0,
                      start_col=1, end_col=1)

    cli_columns([
        str(a) for a in [
            in_file_gz, annotation_file, "-w", workdir, "--grr", grr_file,
            "-o", out_file, "-j 1"
        ]
    ])

    with gzip.open(out_file.with_suffix(".txt.gz"), "rt") as out:
        out_file_content = out.read()
    assert out_file_content == out_expected_content
    assert os.path.exists(out_file_tbi)
    assert os.listdir(workdir) == [
        "tasks-status",  # default task status dir
        # part files must be cleaned up
    ]


def test_annotate_vcf_forbidden_symbol_replacement(
    tmp_path, annotate_directory_fixture
):
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   A   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr1   25  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)

    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    workdir = tmp_path / "output"
    annotation_file = tmp_path / "annotation_forbidden_symbols.yaml"
    grr_file = tmp_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file, annotation_file, "-w", workdir, "--grr", grr_file,
            "-o", out_file
        ]
    ])

    result = []
    # pylint: disable=no-member
    with pysam.VariantFile(out_file) as vcf_file:
        for vcf in vcf_file.fetch():
            result.append(vcf.info["score"][0])
    assert result == ["a|b", "c|d", "e_f"]


def test_annotate_vcf_none_values(tmp_path, annotate_directory_fixture):
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO
        chr1   23  .  C   T   .    .      .
        chr1   24  .  C   A,G,T   .    .      .
        chr1   25  .  C   C,T   .    .      .
        chr1   26  .  C   G   .    .      .
    """)

    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    workdir = tmp_path / "output"
    annotation_file = tmp_path / "annotation_multiallelic.yaml"
    grr_file = tmp_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file, annotation_file, "-w", workdir, "--grr", grr_file,
            "-o", out_file
        ]
    ])

    # pylint: disable=no-member
    with pysam.VariantFile(out_file) as vcf_file:
        variants = [*vcf_file.fetch()]
    assert variants[0].info["score"] == ("0.1",)
    assert variants[1].info["score"] == ("0.3", "0.4", ".")
    assert "score" not in variants[2].info
    assert "score" not in variants[3].info


def test_vcf_description_with_quotes(tmp_path, annotate_directory_fixture):
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   A   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr1   25  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)

    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    workdir = tmp_path / "output"
    annotation_file = tmp_path / "annotation_quotes_in_description.yaml"
    grr_file = tmp_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file, annotation_file, "-w", workdir, "--grr", grr_file,
            "-o", out_file
        ]
    ])

    # pylint: disable=no-member
    with pysam.VariantFile(out_file) as vcf_file:
        info = vcf_file.header.info
    assert info["score"].description == \
        'The \\"phastCons\\" computed over the tree of 100 verterbrate species'  # noqa