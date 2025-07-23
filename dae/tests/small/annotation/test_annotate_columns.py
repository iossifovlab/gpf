# pylint: disable=W0621,C0114,C0116,W0212,W0613
import gzip
import os
import pathlib
import textwrap

import pysam
import pytest
from dae.annotation.annotatable import (
    Annotatable,
    CNVAllele,
    Position,
    Region,
    VCFAllele,
)
from dae.annotation.annotate_columns import cli as cli_columns
from dae.annotation.record_to_annotatable import build_record_to_annotatable
from dae.genomic_resources.genomic_context import (
    GenomicContext,
    SimpleGenomicContext,
)
from dae.genomic_resources.testing import setup_tabix
from dae.testing import setup_denovo, setup_genome


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
    ],
)
def test_default_columns(
        record: dict[str, str], expected: Annotatable) -> None:
    annotatable = build_record_to_annotatable(
        {}, set(record.keys())).build(record)
    assert str(annotatable) == str(expected)


@pytest.mark.parametrize(
    "record,expected", [
        ({"location": "chr1:13", "variant": "sub(A->T)"},
         VCFAllele("chr1", 13, "A", "T")),

        ({"location": "chr1:3-13", "variant": "duplication"},
         CNVAllele("chr1", 3, 13, CNVAllele.Type.LARGE_DUPLICATION)),
    ],
)
def test_cshl_variants_without_context(
        record: dict[str, str], expected: Annotatable) -> None:  # noqa: ARG001
    with pytest.raises(ValueError):  # noqa: PT011
        build_record_to_annotatable(
            {}, set(record.keys())).build(record)


@pytest.fixture
def gc_fixture(tmp_path: pathlib.Path) -> GenomicContext:
    genome = setup_genome(
        tmp_path / "acgt_gpf" / "genome" / "allChr.fa",
        f"""
        >chr1
        {25 * "ACGT"}
        >chr2
        {25 * "ACGT"}
        >chr3
        {25 * "ACGT"}
        """,
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
    ],
)
def test_build_record(
        record: dict[str, str],
        expected: Annotatable,
        gc_fixture: GenomicContext) -> None:
    ref_genome = gc_fixture.get_reference_genome()
    annotatable = build_record_to_annotatable(
        {}, set(record.keys()), ref_genome,
    ).build(record)
    assert str(annotatable) == str(expected)


def test_build_record_to_annotatable_failures() -> None:
    with pytest.raises(
            ValueError, match="no record to annotatable could be found"):
        build_record_to_annotatable({}, set())

    with pytest.raises(
            ValueError, match="no record to annotatable could be found"):
        build_record_to_annotatable({"gosho": "pesho"}, set())


def get_file_content_as_string(file: str) -> str:
    with open(file, "rt", encoding="utf8") as infile:
        return "".join(infile.readlines())


@pytest.mark.parametrize(
    "parameters,record,expected", [
        ({"col_chrom": "chromosome", "col_pos": "position"},
         {"chromosome": "chr1", "position": "4", "ref": "C", "alt": "CT"},
         VCFAllele("chr1", 4, "C", "CT")),
    ],
)
def test_renamed_columns(
        parameters: dict[str, str],
        record: dict[str, str],
        expected: Annotatable) -> None:
    annotatable = build_record_to_annotatable(
        parameters, set(record.keys())).build(record)
    assert str(annotatable) == str(expected)


def test_annotate_columns_basic_setup(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content


def test_annotate_columns_no_header(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        chr1    23
        chr1    24
    """)
    root_path = annotate_directory_fixture
    in_file = root_path / "in.txt"
    out_file = root_path / "out.txt"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    with pytest.raises(
        ValueError,
        match="no record to annotatable could be found",
    ):
        cli_columns([
            str(a) for a in [
                in_file, annotation_file, "--grr", grr_file, "-o", out_file,
                "-w", work_dir,
                "-j", 1,
                "-R", "test_genome",
            ]
        ])


def test_annotate_columns_batch_mode(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--batch-size", 1,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content


def test_annotate_columns_produce_tabix_correctly_position(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """
    Even if the input file has unorthodox columns, if it's tabixed and
    the correct arguments are provided, a tabix file should always be produced.

    This test covers the RecordToPosition annotatable case.
    """

    in_content = textwrap.dedent("""
        #dummyCol1 chrom   dummyCol2 pos  dummyCol3
        ?          chr1    ?         23   ?
        ?          chr1    ?         24   ?
    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt.gz"
    out_file = root_path / "out.txt.gz"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_tabix(in_file, in_content,
                seq_col=1, start_col=3, end_col=3)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    assert len(list(pysam.TabixFile(str(out_file)).fetch())) == 2


def test_annotate_columns_produce_tabix_correctly_vcf_allele(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """
    Even if the input file has unorthodox columns, if it's tabixed and
    the correct arguments are provided, a tabix file should always be produced.

    This test covers the RecordToVcfAllele annotatable case.
    """

    in_content = textwrap.dedent("""
        #dummyCol1 chrom   dummyCol2 pos      dummyCol3  ref  dummyCol4  alt
        ?          chr1    ?         23       ?          A    ?          G
        ?          chr1    ?         24       ?          A    ?          G
    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt.gz"
    out_file = root_path / "out.txt.gz"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_tabix(in_file, in_content,
                seq_col=1, start_col=3, end_col=3)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    assert len(list(pysam.TabixFile(str(out_file)).fetch())) == 2


def test_annotate_columns_produce_tabix_correctly_region_or_cnv_annotatable(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """
    Even if the input file has unorthodox columns, if it's tabixed and
    the correct arguments are provided, a tabix file should always be produced.

    This test covers the RecordToRegion and RecordToCNVAllele annotatable cases.
    """

    in_content = textwrap.dedent("""
        #dummyCol1 chrom   dummyCol2 pos_beg  dummyCol3  pos_end  dummyCol4
        ?          chr1    ?         23       ?          24       ?
        ?          chr1    ?         24       ?          24       ?
    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt.gz"
    out_file = root_path / "out.txt.gz"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_tabix(in_file, in_content,
                seq_col=1, start_col=3, end_col=5)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    assert len(list(pysam.TabixFile(str(out_file)).fetch())) == 2


def test_annotate_columns_idempotence(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    for _ in range(10):
        cli_columns([
            str(a) for a in [
                in_file, annotation_file, "--grr", grr_file, "-o", out_file,
                "-w", work_dir,
                "-j", 1,
                "--force",
                "-R", "test_genome",
            ]
        ])
        out_file_content = get_file_content_as_string(str(out_file))
        assert out_file_content == out_expected_content


def test_annotate_columns_multiple_chrom(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)
    pysam.tabix_compress(str(in_file), str(in_file_gz), force=True)
    pysam.tabix_index(str(in_file_gz), force=True, line_skip=1, seq_col=0,
                      start_col=1, end_col=1)

    cli_columns([
        str(a) for a in [
            in_file_gz, annotation_file, "-w", work_dir, "--grr", grr_file,
            "-o", out_file, "-j", 1, "-R", "test_genome",
        ]
    ])

    with gzip.open(out_file, "rt") as out:
        out_file_content = out.read()
    assert out_file_content == out_expected_content
    assert os.path.exists(out_file_tbi)
    assert set(os.listdir(work_dir)) == {
        ".task-log",     # default task logs dir
        ".task-status",  # default task status dir
        # part files must be cleaned up
    }


def test_annotate_columns_multiple_chrom_repeated_attr(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_duplicate.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)
    pysam.tabix_compress(str(in_file), str(in_file_gz), force=True)
    pysam.tabix_index(str(in_file_gz), force=True, line_skip=1, seq_col=0,
                      start_col=1, end_col=1)

    cli_columns([
        str(a) for a in [
            in_file_gz, annotation_file, "-w", work_dir, "--grr", grr_file,
            "-o", out_file, "-j", 1, "-R", "test_genome",
            "--allow-repeated-attributes",
        ]
    ])

    with gzip.open(out_file, "rt") as out:
        out_file_content = out.read()
    assert out_file_content == out_expected_content
    assert os.path.exists(out_file_tbi)
    assert set(os.listdir(work_dir)) == {
        ".task-log",     # default task logs dir
        ".task-status",  # default task status dir
        # part files must be cleaned up
    }


def test_annotate_columns_none_values(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_multiallelic.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])

    result = pathlib.Path(out_file).read_text()
    assert result == expected


def test_annotate_columns_repeated_attributes(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--allow-repeated-attributes",
            "-R", "test_genome",
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content


def test_annotate_with_pipeline_from_grr(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    pipeline = "res_pipeline"
    grr_file = root_path / "grr.yaml"
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, pipeline, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content


def test_annotate_columns_autodetect_columns_with_underscore(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
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
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content


def test_annotate_columns_float_precision(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
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
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content


def test_annotate_columns_internal_attributes(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
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
    work_dir = tmp_path / "work"

    setup_denovo(in_file, in_content)

    cli_columns([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])
    out_file_content = get_file_content_as_string(str(out_file))
    assert out_file_content == out_expected_content
