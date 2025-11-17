# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
import textwrap
from typing import Any

import dae.annotation.annotate_vcf
import pysam
import pytest
import pytest_mock
from dae.annotation.annotatable import VCFAllele
from dae.annotation.annotate_utils import (
    produce_partfile_paths,
)
from dae.annotation.annotate_vcf import (
    _annotate_vcf,
    _VCFBatchSource,
    _VCFSource,
    _VCFWriter,
    annotate_vcf,
    cli,
)
from dae.annotation.annotation_config import AttributeInfo
from dae.annotation.annotation_factory import (
    build_annotation_pipeline,
)
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genomic_resources.testing import (
    setup_denovo,
    setup_vcf,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing.acgt_import import acgt_gpf
from dae.utils.regions import Region

pytestmark = pytest.mark.usefixtures("clean_genomic_context")


@pytest.fixture
def test_gpf_instance(tmp_path: pathlib.Path) -> GPFInstance:
    score_dir = tmp_path / "acgt_gpf" / "sample_score"
    setup_denovo(
        score_dir / "data.txt",
        textwrap.dedent("""
            chrom  pos_begin  score
            chr1   10         0.1
            chr2   20         0.2
            chr3   30         0.3
        """))
    (score_dir / "genomic_resource.yaml").write_text(textwrap.dedent(
        """
        type: position_score
        table:
            filename: data.txt
        scores:
            - id: score
              type: float
              name: score
        """))
    return acgt_gpf(tmp_path)


@pytest.fixture
def sample_vcf(tmp_path: pathlib.Path) -> pathlib.Path:
    filepath = tmp_path / "sample.vcf"
    setup_vcf(filepath, textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        ##contig=<ID=chr2>
        ##contig=<ID=chr3>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom dad prb
        chr1   10  .  C   T   .    .      .    GT     0/0 0/0 0/1
        chr2   20  .  C   T   .    .      .    GT     0/1 0/0 0/1
        chr3   30  .  C   T   .    .      .    GT     0/1 0/1 0/1
    """))
    return filepath


def test_annotate_vcf_simple(
    tmp_path: pathlib.Path,
    test_gpf_instance: GPFInstance,
    sample_vcf: pathlib.Path,
) -> None:
    out_path = tmp_path / "out.vcf"
    work_dir = tmp_path / "work_dir"
    pipeline_config = [
        {"position_score": "sample_score"},
    ]

    _annotate_vcf(
        str(out_path),
        pipeline_config,
        test_gpf_instance.grr.definition,  # type: ignore
        None,
        {
            "input": str(sample_vcf),
            "reannotate": "",
            "work_dir": str(work_dir),
            "batch_size": 0,
            "region_size": 1,
            "allow_repeated_attributes": False,
            "full_reannotation": False,
            "keep_parts": False,
        },
    )

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_path)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["0.1", "0.2", "0.3"]


def test_annotate_vcf_simple_batch(
    tmp_path: pathlib.Path,
    test_gpf_instance: GPFInstance,
    sample_vcf: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> None:
    out_path = tmp_path / "out.vcf"
    work_dir = tmp_path / "work_dir"
    pipeline_config = [
        {"position_score": "sample_score"},
    ]

    spy = mocker.spy(_VCFBatchSource, "__init__")

    _annotate_vcf(
        str(out_path),
        pipeline_config,
        test_gpf_instance.grr.definition,  # type: ignore
        None,
        {
            "input": str(sample_vcf),
            "reannotate": "",
            "work_dir": str(work_dir),
            "batch_size": 1,
            "region_size": 3_000_000,
            "allow_repeated_attributes": False,
            "full_reannotation": False,
            "keep_parts": False,
        },
    )

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_path)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["0.1", "0.2", "0.3"]

    # assert correct batch size was actually passed to the reader
    assert len(spy.call_args.args) == 2
    assert spy.call_args.kwargs["batch_size"] == 1


def test_basic_vcf(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

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

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["0.1", "0.2"]


def test_batch(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli([
        str(a) for a in [
            in_file,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--batch-size", 1,
        ]
    ])

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6"]


def test_multiallelic_vcf(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO
        chr1   23  .  C   T,A   .    .      .
        chr1   24  .  C   A,G   .    .      .
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_multiallelic.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

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

    result = []
    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [vcf.info["score"] for vcf in vcf_file.fetch()]
    assert result == [("0.1", "0.2"), ("0.3", "0.4")]


def test_vcf_multiple_chroms(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    in_file = tmp_path / "in.vcf.gz"
    out_file = tmp_path / "out.vcf.gz"
    out_file_tbi = tmp_path / "out.vcf.gz.tbi"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

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

    result = []
    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["0.1", "0.2",
                      "0.3", "0.4",
                      "0.5", "0.6"]
    assert os.path.exists(out_file_tbi)
    assert set(os.listdir(work_dir)) == {
        ".task-log",     # default task logs dir
        ".task-status",  # default task status dir
        # part files must be cleaned up
    }


def test_annotate_vcf_float_precision(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr4>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr4   53  .  C   T   .    .      .    GT     0/1 0/0 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

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

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["0.123"]


def test_annotate_vcf_internal_attributes(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_internal_attributes.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

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

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        assert "score_1" in vcf_file.header.info
        assert "score_4" not in vcf_file.header.info
        for rec in vcf_file.fetch():
            assert "score_1" in rec.info
            assert "score_4" not in rec.info


def test_annotate_vcf_forbidden_symbol_replacement(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_forbidden_symbols.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

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

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [vcf.info["score"][0] for vcf in vcf_file.fetch()]
    assert result == ["a|b", "c|d", "e_f"]


def test_annotate_vcf_none_values(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_multiallelic.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

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

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        variants = [*vcf_file.fetch()]
    assert variants[0].info["score"] == ("0.1",)
    assert variants[1].info["score"] == ("0.3", "0.4", ".")
    assert "score" not in variants[2].info
    assert "score" not in variants[3].info


def test_vcf_description_with_quotes(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_quotes_in_description.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

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

    # pylint: disable=no-member
    with pysam.VariantFile(str(out_file)) as vcf_file:
        info = vcf_file.header.info
    assert info["score"].description == \
        'The \\"phastCons\\" computed over the tree of 100 verterbrate species'


def test_annotate_vcf_repeated_attributes(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_repeated_attributes.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli([
        str(a) for a in [
            in_file,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--allow-repeated-attributes",
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


def test_vcf_source_missing_alts(
    tmp_path: pathlib.Path,
) -> None:
    vcf_path = tmp_path / "data.vcf"
    setup_vcf(vcf_path, """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   .   .    .      .    GT     0/0 0/1 0/0
        chr1   25  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)
    with _VCFSource(str(vcf_path)) as source:
        result = list(source.fetch())
        assert len(result) == 2
        assert result[0].annotations[0].annotatable == \
            VCFAllele("chr1", 23, "C", "T")
        assert result[1].annotations[0].annotatable == \
            VCFAllele("chr1", 25, "C", "A")


def test_cli_nonexistent_input_file(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    root_path = annotate_directory_fixture
    in_file = root_path / "blabla_does_not_exist_input.vcf"
    out_file = tmp_path / "out.vcf"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    with pytest.raises(
        ValueError,
        match=r"blabla_does_not_exist_input.vcf does not exist!",
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


def test_writer_does_not_omit_literal_zeros_from_info(
    sample_vcf: pathlib.Path,
) -> None:
    attributes = [
        AttributeInfo("score_1", "source_number",
                      internal=False, parameters={}),
    ]

    with pysam.VariantFile(str(sample_vcf)) as vcf:
        variant = next(vcf.fetch())

    variant.header.info.add("score_1", "A", "String", "blabla")

    _VCFWriter._update_variant(
        variant,
        [{"score_1": 0}],
        attributes,
        [],
    )

    assert variant.info["score_1"] == ("0",)


def test_writer_does_not_write_empty_values_into_info(
    sample_vcf: pathlib.Path,
) -> None:
    attributes = [
        AttributeInfo("score_1", "source_string",
                      internal=False, parameters={}),
        AttributeInfo("score_2", "source_bool",
                      internal=False, parameters={}),
    ]

    with pysam.VariantFile(str(sample_vcf)) as vcf:
        variant = next(vcf.fetch())

    variant.header.info.add("score_1", "A", "String", "blabla")
    variant.header.info.add("score_2", "A", "String", "blabla")

    _VCFWriter._update_variant(
        variant,
        [{"score_1": "", "score_2": False}],
        attributes,
        [],
    )

    assert "score_1" not in variant.info
    assert "score_2" not in variant.info


def test_vcf_region_boundary(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   1   .  C   A   .    .      .    GT     0/1 0/0 0/0
        chr1   2   .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr1   3   .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr1   4   .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr1   5   .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr1   6   .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr1   7   .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf.gz"
    out_file = tmp_path / "out.vcf.gz"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_quotes_in_description.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli([
        str(a) for a in [
            in_file,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--region-size", "2",
        ]
    ])

    variants = 0
    with pysam.VariantFile(str(out_file)) as vcf_file:
        for _ in vcf_file.fetch():
            variants += 1
    assert variants == 7


def test_vcf_keep_parts(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
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
    in_file = tmp_path / "in.vcf.gz"
    out_file = tmp_path / "out.vcf.gz"
    out_file_tbi = tmp_path / "out.vcf.gz.tbi"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli([
        str(a) for a in [
            in_file,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--keep-parts",
        ]
    ])

    assert os.path.exists(out_file)
    assert os.path.exists(out_file_tbi)
    assert set(os.listdir(work_dir)) == {
        ".task-log",     # default task logs dir
        ".task-status",  # default task status dir
        # part files must be kept
        "in.vcf.gz_annotation_chr1_1_47",
        "in.vcf.gz_annotation_chr2_1_47",
        "in.vcf.gz_annotation_chr3_1_47",
    }


def test_vcf_cross_region_boundary(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF    ALT  QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   1   .  CAAAA  C    .    .      .    GT     0/1 0/0 0/0
        chr1   2   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
        chr1   3   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
        chr1   4   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
        chr1   5   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
        chr1   6   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
        chr1   7   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf.gz"
    out_file = tmp_path / "out.vcf.gz"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_quotes_in_description.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    cli([
        str(a) for a in [
            in_file,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--region-size", "2",
        ]
    ])

    variants = 0
    with pysam.VariantFile(str(out_file)) as vcf_file:
        for _ in vcf_file.fetch():
            variants += 1
    assert variants == 7


def test_annotate_vcf_no_regions(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> None:
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF    ALT  QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   1   .  CAAAA  C    .    .      .    GT     0/1 0/0 0/0
        chr1   2   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
        chr1   3   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
        chr1   4   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
        chr1   5   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
        chr1   6   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
        chr1   7   .  CAAAA  C    .    .      .    GT     0/0 0/1 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf.gz"
    out_file = tmp_path / "out.vcf.gz"
    work_dir = tmp_path / "output"
    annotation_file = root_path / "annotation_quotes_in_description.yaml"
    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    spy = mocker.spy(dae.annotation.annotate_vcf, "_annotate_vcf")
    cli([
        str(a) for a in [
            in_file,
            annotation_file,
            "--grr", grr_file,
            "-o", out_file,
            "-w", work_dir,
            "-j", 1,
            "--region-size", "0",
        ]
    ])

    assert spy.call_count == 1


def test_annotate_vcf_version_report(
    capsys: pytest.CaptureFixture,
) -> None:
    capsys.readouterr()

    with pytest.raises(SystemExit):
        cli(["--version"])

    out, _err = capsys.readouterr()
    assert out.startswith("GPF version")


def _build_annotate_vcf_args(**overrides: Any) -> dict[str, Any]:
    """Build args dict for annotate_vcf function with sensible defaults."""
    defaults = {
        "batch_size": 0,
    }
    defaults.update(overrides)
    return defaults


def test_annotate_vcf_function_basic(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_vcf function with basic VCF data."""
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"

    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_vcf function
    args = _build_annotate_vcf_args()

    annotate_vcf(
        str(in_file),
        pipeline,
        str(out_file),
        args,
    )

    # Verify output
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [v.info["score"][0] for v in vcf_file.fetch()]
    assert result == ["0.1", "0.2"]


def test_annotate_vcf_function_with_batch_mode(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test annotate_vcf function with batch processing."""
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"

    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    spy = mocker.spy(_VCFBatchSource, "__init__")

    # Test annotate_vcf function with batch mode
    args = _build_annotate_vcf_args(batch_size=10)

    annotate_vcf(
        str(in_file),
        pipeline,
        str(out_file),
        args,
    )

    # Verify output
    with pysam.VariantFile(str(out_file)) as vcf_file:
        result = [v.info["score"][0] for v in vcf_file.fetch()]
    assert result == ["0.1", "0.2"]

    # Verify batch mode was used
    assert len(spy.call_args.args) == 2
    assert spy.call_args.kwargs["batch_size"] == 10


def test_annotate_vcf_function_with_region(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_vcf function with region parameter."""
    # Note: Region filtering requires indexed VCF
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
        chr1   50  .  G   C   .    .      .    GT     0/1 0/0 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf.gz"
    out_file = tmp_path / "out.vcf"

    grr_file = root_path / "grr.yaml"

    # Create indexed VCF file
    setup_vcf(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_vcf function with region
    # Should only annotate positions 23-30
    args = _build_annotate_vcf_args()

    annotate_vcf(
        str(in_file),
        pipeline,
        str(out_file),
        args,
        region=Region("chr1", 1, 30),
    )

    # Verify output - position 50 should be excluded
    with pysam.VariantFile(str(tmp_path / "out.vcf.gz")) as vcf_file:
        result = [(v.pos, v.info["score"][0]) for v in vcf_file.fetch()]
    assert len(result) == 2
    assert result == [(23, "0.1"), (24, "0.2")]


def test_annotate_vcf_function_with_attributes_to_delete(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_vcf function with attributes_to_delete parameter."""
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##INFO=<ID=old_score,Number=1,Type=Float,Description="Old score">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      old_score=999    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      old_score=888    GT     0/0 0/1 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"

    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_vcf function with attributes to delete
    args = _build_annotate_vcf_args()

    annotate_vcf(
        str(in_file),
        pipeline,
        str(out_file),
        args,
        attributes_to_delete=["old_score"],
    )

    # Verify output - old_score should be removed
    with pysam.VariantFile(str(out_file)) as vcf_file:
        for variant in vcf_file.fetch():
            assert "old_score" not in variant.info
            assert "score" in variant.info


def test_annotate_vcf_function_multiallelic(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_vcf function with multiallelic variants."""
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T,A .    .      .    GT     0/1 0/0 0/0
    """)
    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf"
    out_file = tmp_path / "out.vcf"

    grr_file = root_path / "grr.yaml"

    setup_vcf(in_file, in_content)

    # Build pipeline with allele score
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"allele_score": "two"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_vcf function
    args = _build_annotate_vcf_args()

    annotate_vcf(
        str(in_file),
        pipeline,
        str(out_file),
        args,
    )

    # Verify output - should have two scores for two alleles
    with pysam.VariantFile(str(out_file)) as vcf_file:
        for variant in vcf_file.fetch():
            assert "score" in variant.info
            # Multiallelic should have list of scores
            scores = variant.info["score"]
            assert len(scores) == 2


def test_annotate_vcf_function_with_compressed_input(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_vcf function with compressed input file."""
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf.gz"
    out_file = tmp_path / "out.vcf"

    grr_file = root_path / "grr.yaml"

    # Create compressed input file
    setup_vcf(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_vcf function with compressed input
    args = _build_annotate_vcf_args()

    annotate_vcf(
        str(in_file),
        pipeline,
        str(out_file),
        args,
    )

    # Verify output was compressed
    assert (tmp_path / "out.vcf.gz").exists()

    # Verify content
    with pysam.VariantFile(str(tmp_path / "out.vcf.gz")) as vcf_file:
        result = [v.info["score"][0] for v in vcf_file.fetch()]
    assert result == ["0.1", "0.2"]


def test_annotate_vcf_function_with_compressed_input_output(
    annotate_directory_fixture: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """Test annotate_vcf function with compressed input file."""
    in_content = textwrap.dedent("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chr1>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  c1
        chr1   23  .  C   T   .    .      .    GT     0/1 0/0 0/0
        chr1   24  .  C   A   .    .      .    GT     0/0 0/1 0/0
    """)

    root_path = annotate_directory_fixture
    in_file = tmp_path / "in.vcf.gz"
    out_file = tmp_path / "out.vcf.gz"

    grr_file = root_path / "grr.yaml"

    # Create compressed input file
    setup_vcf(in_file, in_content)

    # Build pipeline
    grr = build_genomic_resource_repository(file_name=str(grr_file))
    pipeline_config = [
        {"position_score": "one"},
    ]
    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
    )

    # Test annotate_vcf function with compressed input
    args = _build_annotate_vcf_args()

    annotate_vcf(
        str(in_file),
        pipeline,
        str(out_file),
        args,
    )

    # Verify output was compressed
    assert (tmp_path / "out.vcf.gz").exists()

    # Verify content
    with pysam.VariantFile(str(tmp_path / "out.vcf.gz")) as vcf_file:
        result = [v.info["score"][0] for v in vcf_file.fetch()]
    assert result == ["0.1", "0.2"]
