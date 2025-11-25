# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0302
import gzip
import logging
import os
import pathlib
import textwrap
from typing import Any

import dae.annotation.annotate_columns
import pysam
import pytest
import pytest_mock
from dae.annotation.annotatable import (
    Annotatable,
    CNVAllele,
    Position,
    Region,
    VCFAllele,
)
from dae.annotation.annotate_columns import (
    _CSVBatchSource,
    _CSVBatchWriter,
    _CSVHeader,
    _CSVSource,
    _CSVWriter,
    annotate_columns,
    cli,
)
from dae.annotation.annotation_factory import (
    build_annotation_pipeline,
)
from dae.annotation.processing_pipeline import (
    Annotation,
    AnnotationsWithSource,
)
from dae.annotation.record_to_annotatable import build_record_to_annotatable
from dae.genomic_resources.genomic_context_base import (
    GenomicContext,
    SimpleGenomicContext,
)
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource_id,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genomic_resources.testing import (
    setup_denovo,
    setup_directories,
    setup_genome,
    setup_gzip,
    setup_tabix,
)
from dae.task_graph.logging import FsspecHandler
from dae.utils.regions import Region as GenomicRegion

pytestmark = pytest.mark.usefixtures("clean_genomic_context")


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
    record: dict[str, str], expected: Annotatable,
) -> None:
    allele = build_record_to_annotatable(
            {}, set(record.keys())).build(record)
    assert str(allele) == str(expected)


@pytest.mark.parametrize(
    "record", [
        {"location": "chr1:13", "variant": "ins(TT)"},
        {"location": "chr1:13", "variant": "del(2)"},
    ],
)
def test_cshl_variants_without_context_indels(
    record: dict[str, str],
) -> None:
    with pytest.raises(
            ValueError, match="genome is required for ins/del variants"):

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
        {"reference_genome": genome}, source="test_gc_fixture")


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


def test_renamed_columns_excludes() -> None:
    record = {
        "chromosome": "chr1",
        "position": "4",
        "ref": "C",
        "alt": "CT",
    }
    annotatable = build_record_to_annotatable(
        {
            "col_chrom": "chromosome",
            "col_pos": "position",
            "col_alt": "-",
        },
        set(record.keys()),
    ).build(record)
    assert str(annotatable) == str(Position("chr1", 4))


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
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
        ]
    ])
    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def test_annotate_columns_batch_mode(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
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
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    spy = mocker.spy(_CSVBatchSource, "__init__")

    cli([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--batch-size", 1,
            "-j", 1,
        ]
    ])
    out_file_content = out_file.read_text()

    assert out_file_content == out_expected_content

    # assert correct batch size was actually passed to the reader
    assert len(spy.call_args.args) == 6
    assert spy.call_args.args[-1] == 1  # the last arg is the batch size


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
    out_file = tmp_path / "out.txt.gz"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_tabix(in_file, in_content,
                seq_col=1, start_col=3, end_col=3)

    cli([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", 1,
        ]
    ])

    assert len(list(pysam.TabixFile(str(out_file)).fetch())) == 2
    assert not (tmp_path / "out.txt").exists()


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
    out_file = tmp_path / "out.txt.gz"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_tabix(in_file, in_content,
                seq_col=1, start_col=3, end_col=3)

    cli([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", 1,
        ]
    ])

    assert len(list(pysam.TabixFile(str(out_file)).fetch())) == 2
    assert not (tmp_path / "out.txt").exists()


def test_annotate_columns_produce_tabix_correctly_region_or_cnv_annotatable(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """
    Even if the input file has unorthodox columns, if it's tabixed and
    the correct arguments are provided, a tabix file should always be produced.

    Covers the RecordToRegion and RecordToCNVAllele annotatable cases.
    """

    in_content = textwrap.dedent("""
        #dummyCol1 chrom   dummyCol2 pos_beg  dummyCol3  pos_end  dummyCol4
        ?          chr1    ?         23       ?          24       ?
        ?          chr1    ?         24       ?          24       ?
    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt.gz"
    out_file = tmp_path / "out.txt.gz"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_tabix(in_file, in_content,
                seq_col=1, start_col=3, end_col=5)

    cli([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", 1,
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
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    for _ in range(10):
        cli([
            str(a) for a in [
                in_file, annotation_file, "--grr", grr_file, "-o", out_file,
                "-w", work_dir,
                "-j", 1,
                "--force",
            ]
        ])
        out_file_content = out_file.read_text()
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
    in_file = tmp_path / "in.txt"
    in_file_gz = in_file.with_suffix(".txt.gz")
    out_file = tmp_path / "out.txt.gz"
    out_file_tbi = tmp_path / "out.txt.gz.tbi"
    work_dir = tmp_path / "output"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)
    pysam.tabix_compress(str(in_file), str(in_file_gz), force=True)
    pysam.tabix_index(str(in_file_gz), force=True, line_skip=1, seq_col=0,
                      start_col=1, end_col=1)

    cli([
        str(a) for a in [
            in_file_gz, annotation_file, "-w", work_dir, "--grr", grr_file,
            "-o", out_file, "-j", 1,
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
    in_file = tmp_path / "in.txt"
    in_file_gz = in_file.with_suffix(".txt.gz")
    out_file = tmp_path / "out.txt.gz"
    out_file_tbi = tmp_path / "out.txt.gz.tbi"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_duplicate.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)
    pysam.tabix_compress(str(in_file), str(in_file_gz), force=True)
    pysam.tabix_index(str(in_file_gz), force=True, line_skip=1, seq_col=0,
                      start_col=1, end_col=1)

    cli([
        str(a) for a in [
            in_file_gz, annotation_file, "-w", work_dir, "--grr", grr_file,
            "-o", out_file, "-j", 1,
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
    in_file = tmp_path / "in.tsv"
    out_file = tmp_path / "out.tsv"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_multiallelic.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli([
        str(a) for a in [
            in_file, annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
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
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation_repeated_attributes.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli([
        str(a) for a in [
            in_file, annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--allow-repeated-attributes",
        ]
    ])
    out_file_content = out_file.read_text()
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
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    pipeline = "res_pipeline"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli([
        str(a) for a in [
            in_file, pipeline, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
        ]
    ])
    out_file_content = out_file.read_text()
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
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
        ]
    ])
    out_file_content = out_file.read_text()
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
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
        ]
    ])
    out_file_content = out_file.read_text()
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
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation_internal_attributes.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
        ]
    ])
    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def test_csv_source(
    tmp_path: pathlib.Path,
) -> None:
    csv_path = tmp_path / "data.csv"
    setup_denovo(csv_path, """
        #chrom  pos
        chr1    1
        chr1    2
        chr1    3
        chr1    4
        chr1    5
        chr1    6
    """)

    with _CSVSource(str(csv_path), None, {}, "\t") as source:
        result = list(source.fetch())
        assert len(result) == 6
        for idx, item in enumerate(result):
            assert item == \
                AnnotationsWithSource(
                    {"chrom": "chr1", "pos": str(idx + 1)},
                    [Annotation(Position("chr1", idx + 1),
                                {"chrom": "chr1", "pos": str(idx + 1)})],
                )


def test_csv_batch_source(
    tmp_path: pathlib.Path,
) -> None:
    csv_path = tmp_path / "data.csv"
    setup_denovo(csv_path, """
        #chrom  pos
        chr1    1
        chr1    2
        chr2    1
        chr2    2
        chr3    1
        chr3    2
    """)

    with _CSVBatchSource(str(csv_path), None, {}, "\t", 2) as source:
        result = list(source.fetch())
        assert len(result) == 3
        for idx, batch in enumerate(result):
            chrom = f"chr{idx + 1}"
            assert batch == (
                AnnotationsWithSource(
                    {"chrom": chrom, "pos": "1"},
                    [Annotation(Position(chrom, 1),
                                {"chrom": chrom, "pos": "1"})],
                ),
                AnnotationsWithSource(
                    {"chrom": chrom, "pos": "2"},
                    [Annotation(Position(chrom, 2),
                                {"chrom": chrom, "pos": "2"})],
                ),
            )


def test_csv_source_no_header_in_file(
    tmp_path: pathlib.Path,
) -> None:
    csv_path = tmp_path / "data.csv"
    setup_denovo(csv_path, """
        chr1    23
        chr1    24
    """)

    with pytest.raises(
        ValueError,
        match="no record to annotatable could be found",
    ), _CSVSource(str(csv_path), None, {}, "\t") as source:
        list(source.fetch())


def test_csv_batch_source_no_header_in_file(
    tmp_path: pathlib.Path,
) -> None:
    csv_path = tmp_path / "data.csv"
    setup_denovo(csv_path, """
        chr1    23
        chr1    24
    """)

    with pytest.raises(
        ValueError,
        match="no record to annotatable could be found",
    ), _CSVBatchSource(str(csv_path), None, {}, "\t", 1) as source:
        list(source.fetch())


def test_csv_source_tabixed_fetch_without_region(
    tmp_path: pathlib.Path,
) -> None:
    csv_path = tmp_path / "data.csv.gz"
    setup_tabix(csv_path, """
        #chrom  pos
        chr1   23
        chr1   24
    """, seq_col=0, start_col=1, end_col=1)

    with _CSVSource(str(csv_path), None, {}, "\t") as source:
        result = list(source.fetch())
        assert len(result) == 2
        assert result[0] == AnnotationsWithSource(
            {"chrom": "chr1", "pos": "23"},
            [Annotation(Position("chr1", 23),
                        {"chrom": "chr1", "pos": "23"})],
        )
        assert result[1] == AnnotationsWithSource(
            {"chrom": "chr1", "pos": "24"},
            [Annotation(Position("chr1", 24),
                        {"chrom": "chr1", "pos": "24"})],
        )


def test_csv_writer_bad_input(tmp_path: pathlib.Path) -> None:
    out_path = str(tmp_path / "data.csv")
    header = _CSVHeader(
        ["chrom", "pos"], ["SCORE"])

    writer = _CSVWriter(str(out_path), "\t", header)
    with pytest.raises(KeyError), writer:
        # no "SCORE" column in input which we're trying to write
        writer.filter(AnnotationsWithSource(
            {"chrom": "chr1", "pos": "23"},
            [Annotation(Position("chr1", 23),
                        {"chrom": "chr1", "pos": "23"})],
        ))


def test_csv_batch_writer_bad_input(tmp_path: pathlib.Path) -> None:
    out_path = str(tmp_path / "data.csv")
    header = _CSVHeader(
        ["chrom", "pos"], ["SCORE"],
    )

    writer = _CSVBatchWriter(str(out_path), "\t", header)
    with pytest.raises(KeyError), writer:
        # no "SCORE" column in input which we're trying to write
        writer.filter([AnnotationsWithSource(
            {"chrom": "chr1", "pos": "23"},
            [Annotation(Position("chr1", 23),
                        {"chrom": "chr1", "pos": "23"})],
        )])


def test_cli_nonexistent_input_file(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    root_path = annotate_directory_fixture
    in_file = tmp_path / "blabla_does_not_exist_input.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    with pytest.raises(
        ValueError,
        match=r"blabla_does_not_exist_input.txt does not exist!",
    ):
        cli([
            str(a) for a in [
                in_file,
                annotation_file,
                "--grr", grr_file,
                "-o", out_file,
                "-w", work_dir,
                "-j", 1,
            ]
        ])


def test_cli_no_pipeline_in_context(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        chrom   pos
        chr1    23
        chr1    24
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    with pytest.raises(
        ValueError,
        match="no valid annotation pipeline configured",
    ):
        cli([
            str(in_file),
            "--grr", str(grr_file),
            "-o", str(out_file),
            "-w", str(work_dir),
            "-j", "1",
        ])


def test_cli_renamed_columns(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        CHROMOSOME   POSITION
        chr1         23
        chr1         24
    """)
    out_expected_content = (
        "CHROMOSOME\tPOSITION\tscore\n"
        "chr1\t23\t0.1\n"
        "chr1\t24\t0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli([
        str(a) for a in [
            in_file,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--col-chrom", "CHROMOSOME",
            "--col-pos", "POSITION",
        ]
    ])
    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def test_cli_annotatables_that_need_ref_genome(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        location  variant
        chr1:23   sub(C->T)
        chr1:24   sub(C->A)
        chr2:33   ins(AAA)
        chr2:34   del(3)
    """)
    out_expected_content = (
        "location\tvariant\tscore\n"
        "chr1:23\tsub(C->T)\t0.1\n"
        "chr1:24\tsub(C->A)\t0.2\n"
        "chr2:33\tins(AAA)\t0.3\n"
        "chr2:34\tdel(3)\t0.35\n"
    )
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "--col-location", "location",
            "--col-variant", "variant",
            "-w", work_dir,
            "-j", 1,
            "-R", "test_genome",
        ]
    ])
    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def test_annotate_columns_concatenate_empty_regions(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        #chrom   pos
        chr1      3
        chr1      4
        chr1      53
        chr1      54

    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt.gz"
    out_file = tmp_path / "out.txt.gz"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_tabix(in_file, in_content,
                seq_col=0, start_col=1, end_col=1)

    cli([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--region-size", 5,
            "-j", 1,
        ]
    ])

    with gzip.open(str(out_file), "rt") as res:
        out_file_content = res.readlines()
        assert len(out_file_content) == 5


def test_annotate_columns_region_boundary(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        #chrom   pos
        chr1      1
        chr1      2
        chr1      3
        chr1      4
        chr1      5
        chr1      51
        chr1      52

    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt.gz"
    out_file = tmp_path / "out.txt.gz"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_tabix(in_file, in_content,
                seq_col=0, start_col=1, end_col=1)

    cli([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--region-size", 2,
            "-j", 1,
        ]
    ])

    with gzip.open(str(out_file), "rt") as res:
        out_file_content = res.readlines()
        assert len(out_file_content) == 8


def test_annotate_columns_keep_parts(
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

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    in_file_gz = in_file.with_suffix(".txt.gz")
    out_file = tmp_path / "out.txt.gz"
    out_file_tbi = tmp_path / "out.txt.gz.tbi"
    work_dir = tmp_path / "output"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)
    pysam.tabix_compress(str(in_file), str(in_file_gz), force=True)
    pysam.tabix_index(str(in_file_gz), force=True, line_skip=1, seq_col=0,
                      start_col=1, end_col=1)

    cli([
        str(a) for a in [
            in_file_gz, annotation_file, "-w", work_dir, "--grr", grr_file,
            "-o", out_file, "-j", 1,
            "--keep-parts",
        ]
    ])

    assert os.path.exists(out_file)
    assert os.path.exists(out_file_tbi)
    assert set(os.listdir(work_dir)) == {
        ".task-log",     # default task logs dir
        ".task-status",  # default task status dir
        # part files must be kept
        "in.txt.gz_annotation_chr1_1_47",
        "in.txt.gz_annotation_chr2_1_47",
        "in.txt.gz_annotation_chr3_1_47",
    }


@pytest.mark.parametrize("verbosity, expected_level", [
    ("", logging.WARNING),
    ("-v", logging.INFO),
    ("-vv", logging.DEBUG),
    ("-vvv", logging.DEBUG),
    ("-vvvv", logging.DEBUG),
])
def test_annotate_columns_logging_level(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
    verbosity: str,
    expected_level: int,
) -> None:
    in_content = textwrap.dedent("""
        chrom   pos
        chr1    23
        chr1    24
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"
    log_file = tmp_path / "log.txt"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    handler = FsspecHandler(str(log_file))
    mocker.patch(
        "dae.task_graph.logging.FsspecHandler",
        return_value=handler,
    )

    cli([
        str(a) for a in [
            in_file, annotation_file, "--grr", grr_file, "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            verbosity,
        ] if a
    ])

    assert handler.level == expected_level


def test_annotate_columns_append_columns(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        chrom   pos  score
        chr1    23   1.0
        chr1    24   2.0
    """)
    out_expected_content = (
        "chrom\tpos\tscore\tscore\n"
        "chr1\t23\t1.0\t0.1\n"
        "chr1\t24\t2.0\t0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    cli([
        str(a) for a in [
            in_file,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
        ]
    ])
    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


@pytest.mark.parametrize("sep", [",", ";", "\t"])
def test_annotate_columns_adjust_output_separator(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
    sep: str,
) -> None:
    in_content = (
        f"chrom{sep}pos{sep}score\n"
        f"chr1{sep}23{sep}1.0\n"
        f"chr1{sep}24{sep}2.0\n"
    )
    out_expected_content = (
        f"chrom{sep}pos{sep}score{sep}score\n"
        f"chr1{sep}23{sep}1.0{sep}0.1\n"
        f"chr1{sep}24{sep}2.0{sep}0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_directories(in_file, in_content)

    cli([
        str(a) for a in [
            in_file,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--in-sep", sep,
        ]
    ])
    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


@pytest.mark.parametrize(
    "isep,osep", [
        (",", ";"),
        ("\t", ","),
        (",", "\t"),
    ])
def test_annotate_columns_output_separator(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
    isep: str,
    osep: str,
) -> None:
    in_content = (
        f"chrom{isep}pos{isep}score\n"
        f"chr1{isep}23{isep}1.0\n"
        f"chr1{isep}24{isep}2.0\n"
    )
    out_expected_content = (
        f"chrom{osep}pos{osep}score{osep}score\n"
        f"chr1{osep}23{osep}1.0{osep}0.1\n"
        f"chr1{osep}24{osep}2.0{osep}0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_directories(in_file, in_content)

    cli([
        str(a) for a in [
            in_file,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--in-sep", isep,
            "--out-sep", osep,
        ]
    ])
    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def test_annotate_columns_cross_region_boundary(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        #chrom    pos   pos_end
        chr1      21    25
        chr1      22    26
        chr1      23    27
        chr1      24    28
        chr1      25    29
    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt.gz"
    out_file = tmp_path / "out.txt.gz"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_tabix(in_file, in_content,
                seq_col=0, start_col=1, end_col=2)

    cli([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--region-size", 2,
            "-j", 1,
        ]
    ])

    with gzip.open(str(out_file), "rt") as res:
        out_file_content = res.readlines()
        assert len(out_file_content) == 6


def test_annotate_columns_no_regions(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> None:
    in_content = textwrap.dedent("""
        #chrom    pos   pos_end
        chr1      21    25
        chr1      22    26
        chr1      23    27
        chr1      24    28
        chr1      25    29
    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt.gz"
    out_file = tmp_path / "out.txt.gz"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_tabix(in_file, in_content,
                seq_col=0, start_col=1, end_col=2)

    spy = mocker.spy(
        dae.annotation.annotate_columns, "_annotate_csv")

    cli([
        str(a) for a in [
            in_file, annotation_file, "-o", out_file,
            "-w", work_dir,
            "--grr", grr_file,
            "--region-size", 0,
            "-j", 1,
        ]
    ])

    assert spy.call_count == 1


def test_annotate_columns_version_report(
    capsys: pytest.CaptureFixture,
) -> None:
    capsys.readouterr()

    with pytest.raises(SystemExit):
        cli(["--version"])

    out, _err = capsys.readouterr()
    assert out.startswith("GPF version")


def test_cli_annotatables_that_need_ref_genome_but_do_not_have_it(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        location  variant
        chr1:23   sub(C->T)
        chr1:24   sub(C->A)
        chr2:33   ins(AAA)
        chr2:34   del(3)
    """)
    out_expected_content = (
        "location\tvariant\tscore\n"
        "chr1:23\tsub(C->T)\t0.1\n"
        "chr1:24\tsub(C->A)\t0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    with pytest.raises(
        ValueError,
        match=r"errors occured during reading of CSV file .*"
        r"genome is required for ins/del variants",
    ):
        cli([
            str(a) for a in [
                in_file, annotation_file, "--grr", grr_file, "-o", out_file,
                "--col-location", "location",
                "--col-variant", "variant",
                "-w", work_dir,
                "-j", 1,
            ]
        ])
    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def test_cli_annotatables_dae_that_need_ref_genome_but_do_not_have_it(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        chr   pos   variant
        chr1  23   sub(C->T)
        chr1  24   sub(C->A)
        chr2  33   ins(AAA)
        chr2  34   del(3)
    """)
    out_expected_content = (
        "chr\tpos\tvariant\tscore\n"
        "chr1\t23\tsub(C->T)\t0.1\n"
        "chr1\t24\tsub(C->A)\t0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"
    work_dir = tmp_path / "work"

    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    with pytest.raises(
        ValueError,
        match=r"errors occured during reading of CSV file .*"
        r"genome is required for ins/del variants",
    ):
        cli([
            str(a) for a in [
                in_file, annotation_file, "--grr", grr_file, "-o", out_file,
                "--col-chrom", "chr",
                "--col-pos", "pos",
                "--col-variant", "variant",
                "-w", work_dir,
                "-j", 1,
            ]
        ])
    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def _build_annotate_columns_args(**overrides: Any) -> dict[str, Any]:
    """Build args dict for annotate_columns function with sensible defaults."""
    defaults = {
        "input_separator": "\t",
        "output_separator": "\t",
        "batch_size": 0,
        "columns_args": {
            "col_chrom": "chrom",
            "col_pos": "pos",
            "col_pos_beg": "pos_beg",
            "col_pos_end": "pos_end",
            "col_ref": "ref",
            "col_alt": "alt",
            "col_location": "location",
            "col_variant": "variant",
            "col_vcf_like": "vcf_like",
            "col_cnv_type": "cnv_type",
        },
    }
    defaults.update(overrides)
    return defaults


def test_annotate_columns_function_basic(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_columns function with basic position data."""

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
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"

    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_columns function
    args = _build_annotate_columns_args()

    annotate_columns(
        str(in_file),
        pipeline,
        str(out_file),
        args,
    )

    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def test_annotate_columns_function_with_batch_mode(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test annotate_columns function with batch processing."""
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
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"

    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    spy = mocker.spy(_CSVBatchSource, "__init__")

    # Test annotate_columns function with batch mode
    args = _build_annotate_columns_args(batch_size=10)

    annotate_columns(
        str(in_file),
        pipeline,
        str(out_file),
        args,
    )

    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content

    # Verify batch mode was used
    assert len(spy.call_args.args) == 6
    assert spy.call_args.args[5] == 10  # batch_size is the 6th positional arg


def test_annotate_columns_function_with_vcf_alleles(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_columns function with VCF alleles."""
    in_content = textwrap.dedent("""
        chrom   pos   ref   alt
        chr1    23    C     T
        chr1    24    C     A
    """)
    out_expected_content = (
        "chrom\tpos\tref\talt\tscore\n"
        "chr1\t23\tC\tT\t0.1\n"
        "chr1\t24\tC\tA\t0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"

    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_columns function
    args = _build_annotate_columns_args()

    annotate_columns(
        str(in_file),
        pipeline,
        str(out_file),
        args,
    )

    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def test_annotate_columns_function_with_region(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_columns function - region parameter is accepted."""

    # Note: Region filtering only works with tabix-indexed files in the
    # full CLI workflow. For the direct function call, we just verify
    # the parameter is accepted without error.
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
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"

    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_columns function - region parameter is accepted
    args = _build_annotate_columns_args()

    annotate_columns(
        str(in_file),
        pipeline,
        str(out_file),
        args,
        region=GenomicRegion("chr1", 1, 30),
    )

    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def test_annotate_columns_function_with_attributes_to_delete(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_columns function with attributes_to_delete parameter."""
    in_content = textwrap.dedent("""
        chrom   pos   old_score
        chr1    23    999
        chr1    24    888
    """)
    out_expected_content = (
        "chrom\tpos\tscore\n"
        "chr1\t23\t0.1\n"
        "chr1\t24\t0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"

    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_columns function with attributes to delete
    args = _build_annotate_columns_args()

    annotate_columns(
        str(in_file),
        pipeline,
        str(out_file),
        args,
        attributes_to_delete=["old_score"],
    )

    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def test_annotate_columns_function_with_compressed_input(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_columns function with compressed input file."""
    in_content = textwrap.dedent("""
        chrom   pos
        chr1    23
        chr1    24
    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt.gz"
    out_file = tmp_path / "out.txt"

    grr_file = root_path / "grr.yaml"

    # Create compressed input file (gzipped without tabix index)
    setup_gzip(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_columns function with compressed input
    args = _build_annotate_columns_args()

    annotate_columns(
        str(in_file),
        pipeline,
        str(out_file),
        args,
    )

    # Verify output was compressed
    assert (tmp_path / "out.txt.gz").exists()

    # Verify content
    with gzip.open(tmp_path / "out.txt.gz", "rt") as f:
        out_file_content = f.read()

    assert "chrom\tpos\tscore\n" in out_file_content
    assert "chr1\t23\t0.1\n" in out_file_content
    assert "chr1\t24\t0.2\n" in out_file_content


def test_annotate_columns_function_with_reference_genome(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_columns function with reference genome for CSHL format."""
    in_content = textwrap.dedent("""
        location  variant
        chr1:23   sub(C->T)
        chr1:24   sub(C->A)
    """)
    out_expected_content = (
        "location\tvariant\tscore\n"
        "chr1:23\tsub(C->T)\t0.1\n"
        "chr1:24\tsub(C->A)\t0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt"
    out_file = tmp_path / "out.txt"

    grr_file = root_path / "grr.yaml"

    setup_denovo(in_file, in_content)

    # Build pipeline and get reference genome
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    ref_genome = build_reference_genome_from_resource_id(
        "test_genome", grr,
    )
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_columns function with reference genome
    args = _build_annotate_columns_args()

    annotate_columns(
        str(in_file),
        pipeline,
        str(out_file),
        args,
        reference_genome=ref_genome,
    )

    out_file_content = out_file.read_text()
    assert out_file_content == out_expected_content


def test_annotate_columns_function_with_compressed_input_output(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_columns function with reference genome for CSHL format."""
    in_content = textwrap.dedent("""
        location  variant
        chr1:23   sub(C->T)
        chr1:24   sub(C->A)
    """)
    out_expected_content = (
        "location\tvariant\tscore\n"
        "chr1:23\tsub(C->T)\t0.1\n"
        "chr1:24\tsub(C->A)\t0.2\n"
    )
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.txt.gz"
    out_file = tmp_path / "out.txt.gz"

    grr_file = root_path / "grr.yaml"

    setup_gzip(in_file, in_content)

    # Build pipeline and get reference genome
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    ref_genome = build_reference_genome_from_resource_id(
        "test_genome", grr,
    )
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_columns function with reference genome
    args = _build_annotate_columns_args()

    annotate_columns(
        str(in_file),
        pipeline,
        str(out_file),
        args,
        reference_genome=ref_genome,
    )

    with gzip.open(str(out_file), "rt") as result:
        out_file_content = result.read()
    assert out_file_content == out_expected_content
