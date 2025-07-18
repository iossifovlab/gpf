# pylint: disable=W0621,C0114,C0116,W0212,W0613
import gzip
import os
import pathlib
import textwrap

import dae.annotation.annotatable
import pysam
import pytest
from dae.annotation.annotatable import Annotatable, Position, VCFAllele
from dae.annotation.annotate_columns import cli as cli_columns
from dae.annotation.annotate_vcf import cli as cli_vcf
from dae.annotation.annotate_vcf import produce_partfile_paths
from dae.annotation.record_to_annotatable import build_record_to_annotatable
from dae.genomic_resources.testing import setup_genome, setup_pedigree
from dae.testing import setup_denovo, setup_directories, setup_vcf
from dae.utils.regions import Region


@pytest.mark.parametrize(
    "record,expected", [
        ({"chrom": "chr1", "pos": "3"},
         Position("chr1", 3)),

        ({"chrom": "chr1", "pos": "4", "ref": "C", "alt": "CT"},
         VCFAllele("chr1", 4, "C", "CT")),

        ({"vcf_like": "chr1:4:C:CT"},
         VCFAllele("chr1", 4, "C", "CT")),

        ({"chrom": "chr1", "pos_beg": "4", "pos_end": "30"},
         dae.annotation.annotatable.Region("chr1", 4, 30)),
    ],
)
def test_default_columns(
        record: dict[str, str], expected: Annotatable) -> None:
    annotatable = build_record_to_annotatable(
        {}, set(record.keys())).build(record)
    assert str(annotatable) == str(expected)


@pytest.mark.parametrize(
    "parameters,record,expected", [
        ({"col_chrom": "chromosome", "col_pos": "position"},
         {"chromosome": "chr1", "position": "4", "ref": "C", "alt": "CT"},
         VCFAllele("chr1", 4, "C", "CT")),
    ],
)
def test_renamed_columns(
        parameters: dict[str, str], record: dict[str, str],
        expected: Annotatable) -> None:
    annotatable = build_record_to_annotatable(
        parameters, set(record.keys())).build(record)
    assert str(annotatable) == str(expected)


def test_build_record_to_annotable_failures() -> None:
    with pytest.raises(
            ValueError, match="no record to annotatable could be found"):
        build_record_to_annotatable({}, set())

    with pytest.raises(
            ValueError, match="no record to annotatable could be found"):
        build_record_to_annotatable({"gosho": "pesho"}, set())


def get_file_content_as_string(file: str) -> str:
    with open(file, "rt", encoding="utf8") as infile:
        return "".join(infile.readlines())


@pytest.fixture
def annotate_directory_fixture(tmp_path: pathlib.Path) -> pathlib.Path:
    root_path = tmp_path / "annotate_columns_and_vcf"
    setup_directories(
        root_path,
        {
            "annotation.yaml": """
                - position_score: one
            """,
            "annotation_duplicate.yaml": """
                - position_score: one
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
            "annotation_repeated_attributes.yaml": """
                - position_score: one
                - position_score: four
            """,
            "annotation_internal_attributes.yaml": """
                - position_score:
                    resource_id: one
                    attributes:
                    - source: score
                      name: score_1
                - position_score:
                    resource_id: four
                    attributes:
                    - source: score
                      name: score_4
                      internal: true
            """,
            "grr.yaml": f"""
                id: mm
                type: dir
                directory: "{root_path}/grr"
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
                    """,
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
                    """,
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
                    """,
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
                    """,
                },
                "res_pipeline": {
                    "annotation.yaml": """
                        - position_score: one
                    """,
                    "genomic_resource.yaml": """
                        type: annotation_pipeline
                        filename: annotation.yaml
                    """,
                },
                "test_genome": {
                    "genomic_resource.yaml": """
                        type: genome
                        filename: genome.fa
                    """,
                },
            },
        },
    )
    one_content = textwrap.dedent("""
        chrom  pos_begin  s1
        chr1   23         0.1
        chr1   24         0.2
        chr2   33         0.3
        chr2   34         0.4
        chr3   43         0.5
        chr3   44         0.6
        chr4   53         0.1234567890123456789
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
    four_content = textwrap.dedent("""
        chrom  pos_begin  s1
        chr1   23         0.101
        chr1   24         0.201
        chr2   33         0.301
        chr2   34         0.401
        chr3   43         0.501
        chr3   44         0.601
    """)
    setup_denovo(root_path / "grr" / "one" / "data.txt", one_content)
    setup_denovo(root_path / "grr" / "two" / "data.txt", two_content)
    setup_denovo(root_path / "grr" / "three" / "data.txt", three_content)
    setup_denovo(root_path / "grr" / "four" / "data.txt", four_content)
    setup_genome(root_path / "grr" / "test_genome" / "genome.fa",
                 textwrap.dedent(f"""
                     >chr1
                     {25 * 'ACGT'}
                     >chr2
                     {25 * 'ACGT'}
                     >chr3
                     {25 * 'ACGT'}
                     >chr4
                     {25 * 'ACGT'}
                 """))
    return root_path


@pytest.fixture
def sample_ped(tmp_path: pathlib.Path) -> pathlib.Path:
    filepath = tmp_path / "sample.ped"
    setup_pedigree(filepath, textwrap.dedent("""
        familyId personId dadId momId sex status role
        f1       m1       0     0     2   1      mom
        f1       d1       0     0     1   1      dad
        f1       c1       dad   mom   1   2      prb
    """))
    return filepath


def test_annotate_columns_basic_setup(
        annotate_directory_fixture: pathlib.Path) -> None:
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
    root_path = annotate_directory_fixture
    in_file = root_path / "in.txt"
    out_file = root_path / "out.txt"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"
    work_dir = root_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content


def test_annotate_columns_idempotence(
    annotate_directory_fixture: pathlib.Path,
) -> None:
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
    root_path = annotate_directory_fixture
    in_file = root_path / "in.txt"
    out_file = root_path / "out.txt"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"
    work_dir = root_path / "work"

    setup_denovo(in_file, in_content)

    for _ in range(10):
        cli_columns([
            str(a) for a in [
                in_file, annotation_file, "--grr", grr_file, "-o", out_file,
                "-w", work_dir,
                "-j", 1,
                "--force",
            ]
        ])
        out_file_content = get_file_content_as_string(str(out_file))
        assert out_file_content == out_expected_content


def test_annotate_columns_multiple_chrom(
    annotate_directory_fixture: pathlib.Path,
) -> None:
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
    root_path = annotate_directory_fixture
    in_file = root_path / "in.txt"
    in_file_gz = in_file.with_suffix(".txt.gz")
    out_file = root_path / "out.txt.gz"
    out_file_tbi = root_path / "out.txt.gz.tbi"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)
    pysam.tabix_compress(str(in_file), str(in_file_gz), force=True)
    pysam.tabix_index(str(in_file_gz), force=True, line_skip=1, seq_col=0,
                      start_col=1, end_col=1)

    cli_columns([
        str(a) for a in [
            in_file_gz, annotation_file, "-w", workdir, "--grr", grr_file,
            "-o", out_file, "-j", 1, "-R", "test_genome",
        ]
    ])

    with gzip.open(out_file, "rt") as out:
        out_file_content = out.read()
    assert out_file_content == out_expected_content
    assert os.path.exists(out_file_tbi)
    assert set(os.listdir(workdir)) == {
        ".task-log",     # default task logs dir
        ".task-status",  # default task status dir
        # part files must be cleaned up
    }


def test_annotate_columns_multiple_chrom_repeated_attr(
    annotate_directory_fixture: pathlib.Path,
) -> None:
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
        "chrom\tpos\tscore_A0\tscore_A1\n"
        "chr1\t23\t0.1\t0.1\n"
        "chr1\t24\t0.2\t0.2\n"
        "chr2\t33\t0.3\t0.3\n"
        "chr2\t34\t0.4\t0.4\n"
        "chr3\t43\t0.5\t0.5\n"
        "chr3\t44\t0.6\t0.6\n"
    )
    root_path = annotate_directory_fixture
    in_file = root_path / "in.txt"
    in_file_gz = in_file.with_suffix(".txt.gz")
    out_file = root_path / "out.txt.gz"
    out_file_tbi = root_path / "out.txt.gz.tbi"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation_duplicate.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)
    pysam.tabix_compress(str(in_file), str(in_file_gz), force=True)
    pysam.tabix_index(str(in_file_gz), force=True, line_skip=1, seq_col=0,
                      start_col=1, end_col=1)

    cli_columns([
        str(a) for a in [
            in_file_gz, annotation_file, "-w", workdir, "--grr", grr_file,
            "-o", out_file, "-j", 1, "-R", "test_genome",
            "--allow-repeated-attributes",
        ]
    ])

    with gzip.open(out_file, "rt") as out:
        out_file_content = out.read()
    assert out_file_content == out_expected_content
    assert os.path.exists(out_file_tbi)
    assert set(os.listdir(workdir)) == {
        ".task-log",     # default task logs dir
        ".task-status",  # default task status dir
        # part files must be cleaned up
    }


def test_annotate_columns_none_values(
    annotate_directory_fixture: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        chrom  pos        ref        alt
        chr1   23         C          T
        chr1   24         C          A
        chr1   24         C          G
        chr1   24         C          T
        chr1   25         C          T
        chr1   26         C          G
    """)
    expected = (
        "chrom\tpos\tref\talt\tscore\n"
        "chr1\t23\tC\tT\t0.1\n"
        "chr1\t24\tC\tA\t0.3\n"
        "chr1\t24\tC\tG\t0.4\n"
        "chr1\t24\tC\tT\t\n"
        "chr1\t25\tC\tT\t\n"
        "chr1\t26\tC\tG\t\n"
    )
    root_path = annotate_directory_fixture
    in_file = root_path / "in.tsv"
    out_file = root_path / "out.tsv"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation_multiallelic.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", workdir,
            "-j", 1,
        ]
    ])

    result = pathlib.Path(out_file).read_text()
    assert result == expected


def test_annotate_columns_repeated_attributes(
    annotate_directory_fixture: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        chrom   pos
        chr1    23
        chr1    24
    """)
    out_expected_content = (
        "chrom\tpos\tscore_A0\tscore_A1\n"
        "chr1\t23\t0.1\t0.101\n"
        "chr1\t24\t0.2\t0.201\n"
    )
    root_path = annotate_directory_fixture
    in_file = root_path / "in.txt"
    out_file = root_path / "out.txt"
    annotation_file = root_path / "annotation_repeated_attributes.yaml"
    grr_file = root_path / "grr.yaml"
    work_dir = root_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--allow-repeated-attributes",
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content


def test_annotate_with_pipeline_from_grr(
        annotate_directory_fixture: pathlib.Path) -> None:
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
    root_path = annotate_directory_fixture
    in_file = root_path / "in.txt"
    out_file = root_path / "out.txt"
    pipeline = "res_pipeline"
    grr_file = root_path / "grr.yaml"
    work_dir = root_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, pipeline, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content


def test_annotate_columns_autodetect_columns_with_underscore(
        annotate_directory_fixture: pathlib.Path) -> None:
    in_content = textwrap.dedent("""
        chrom   pos_beg   pos_end
        chr1    23        23
        chr1    24        24
    """)
    out_expected_content = (
        "chrom\tpos_beg\tpos_end\tscore\n"
        "chr1\t23\t23\t0.1\n"
        "chr1\t24\t24\t0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = root_path / "in.txt"
    out_file = root_path / "out.txt"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"
    work_dir = root_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content


def test_annotate_columns_float_precision(
        annotate_directory_fixture: pathlib.Path) -> None:
    in_content = textwrap.dedent("""
        chrom   pos
        chr4    53
    """)
    out_expected_content = (
        "chrom\tpos\tscore\n"
        "chr4\t53\t0.123\n"
    )
    root_path = annotate_directory_fixture
    in_file = root_path / "in.txt"
    out_file = root_path / "out.txt"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"
    work_dir = root_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content


def test_annotate_columns_internal_attributes(
        annotate_directory_fixture: pathlib.Path) -> None:
    in_content = textwrap.dedent("""
        chrom   pos
        chr1    23
        chr1    24
    """)
    out_expected_content = (
        "chrom\tpos\tscore_1\n"
        "chr1\t23\t0.1\n"
        "chr1\t24\t0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = root_path / "in.txt"
    out_file = root_path / "out.txt"
    annotation_file = root_path / "annotation_internal_attributes.yaml"
    grr_file = root_path / "grr.yaml"
    work_dir = root_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content

# ===============================
# VCF ANNOTATION TOOL TESTS BELOW
# ===============================


def test_basic_vcf(
    annotate_directory_fixture: pathlib.Path,
    sample_ped: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = root_path / "in.vcf"
    out_file = root_path / "out.vcf"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file,
            sample_ped,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", workdir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["0.1", "0.2"]


def test_multiallelic_vcf(
    annotate_directory_fixture: pathlib.Path,
    sample_ped: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO
        chr1   23  .  C   T,A   .    .      .
        chr1   24  .  C   A,G   .    .      .
    """)
    root_path = annotate_directory_fixture
    in_file = root_path / "in.vcf"
    out_file = root_path / "out.vcf"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation_multiallelic.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file,
            sample_ped,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", workdir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    result = []
    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [vcf.info["score"] for vcf in vcf_file.fetch()]
    assert result == [("0.1", "0.2"), ("0.3", "0.4")]


def test_vcf_multiple_chroms(
    annotate_directory_fixture: pathlib.Path,
    sample_ped: pathlib.Path,
) -> None:
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
    root_path = annotate_directory_fixture
    in_file = root_path / "in.vcf.gz"
    out_file = root_path / "out.vcf.gz"
    out_file_tbi = root_path / "out.vcf.gz.tbi"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file,
            sample_ped,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", workdir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    result = []
    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["0.1", "0.2",
                      "0.3", "0.4",
                      "0.5", "0.6"]
    assert os.path.exists(out_file_tbi)
    assert set(os.listdir(workdir)) == {
        ".task-log",     # default task logs dir
        ".task-status",  # default task status dir
        # part files must be cleaned up
    }


def test_annotate_vcf_float_precision(
    annotate_directory_fixture: pathlib.Path,
    sample_ped: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr4>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr4   53  .  C   T   .    .      .    GT     0/1 0/0 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = root_path / "in.vcf"
    out_file = root_path / "out.vcf"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file,
            sample_ped,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", workdir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["0.123"]


def test_annotate_vcf_internal_attributes(
    annotate_directory_fixture: pathlib.Path,
    sample_ped: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = root_path / "in.vcf"
    out_file = root_path / "out.vcf"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation_internal_attributes.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file,
            sample_ped,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", workdir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        for rec in vcf_file.fetch():
            assert "score_1" in rec.info
            assert "score_4" not in rec.info


def test_annotate_vcf_forbidden_symbol_replacement(
    annotate_directory_fixture: pathlib.Path,
    sample_ped: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   A   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr1   25  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = root_path / "in.vcf"
    out_file = root_path / "out.vcf"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation_forbidden_symbols.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file,
            sample_ped,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", workdir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["a|b", "c|d", "e_f"]


def test_annotate_vcf_none_values(
    annotate_directory_fixture: pathlib.Path,
    sample_ped: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO
        chr1   23  .  C   T   .    .      .
        chr1   24  .  C   A,G,T   .    .      .
        chr1   25  .  C   C,T   .    .      .
        chr1   26  .  C   G   .    .      .
    """)
    root_path = annotate_directory_fixture
    in_file = root_path / "in.vcf"
    out_file = root_path / "out.vcf"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation_multiallelic.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file,
            sample_ped,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", workdir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        variants = [*vcf_file.fetch()]
    assert variants[0].info["score"] == ("0.1",)
    assert variants[1].info["score"] == ("0.3", "0.4", ".")
    assert "score" not in variants[2].info
    assert "score" not in variants[3].info


def test_vcf_description_with_quotes(
    annotate_directory_fixture: pathlib.Path,
    sample_ped: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   A   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr1   25  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = root_path / "in.vcf"
    out_file = root_path / "out.vcf"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation_quotes_in_description.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file,
            sample_ped,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", workdir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        info = vcf_file.header.info
    assert info["score"].description == \
        'The \\"phastCons\\" computed over the tree of 100 verterbrate species'


def test_annotate_vcf_repeated_attributes(
    annotate_directory_fixture: pathlib.Path,
    sample_ped: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = root_path / "in.vcf"
    out_file = root_path / "out.vcf"
    workdir = root_path / "output"
    annotation_file = root_path / "annotation_repeated_attributes.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli_vcf([
        str(a) for a in [
            in_file,
            sample_ped,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", workdir,
            "-j", 1,
            "--allow-repeated-attributes",
            "-R", "test_genome",
        ]
    ])

    result = []
    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        for vcf in vcf_file.fetch():
            result.extend([
                vcf.info["score_A0"][0],
                vcf.info["score_A1"][0],
            ])
    assert result == ["0.1", "0.101", "0.2", "0.201"]


def test_produce_partfile_paths() -> None:
    regions = [Region("chr1", 0, 1000),
               Region("chr1", 1000, 2000),
               Region("chr1", 2000, 3000)]
    expected_output = [
        "work_dir/output/input.vcf_annotation_chr1_0_1000",
        "work_dir/output/input.vcf_annotation_chr1_1000_2000",
        "work_dir/output/input.vcf_annotation_chr1_2000_3000",
    ]
    # relative input file path
    assert produce_partfile_paths(
        "src/input.vcf", regions, "work_dir/output",
    ) == expected_output
    # absolute input file path
    assert produce_partfile_paths(
        "/home/user/src/input.vcf", regions, "work_dir/output",
    ) == expected_output

# =============================
# VCF ANNOTATION TOOL TESTS END
# =============================
