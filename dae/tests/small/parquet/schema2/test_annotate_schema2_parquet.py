# pylint: disable=W0621,C0114,C0116,W0212,W0613
import io
import pathlib
import textwrap
from collections.abc import Callable
from contextlib import redirect_stdout
from datetime import datetime
from glob import glob

import pytest
import pytest_mock
from dae.annotation.annotation_pipeline import ReannotationPipeline
from dae.annotation.score_annotator import PositionScoreAnnotator
from dae.genomic_resources.genomic_context import GenomicContext
from dae.gpf_instance import GPFInstance
from dae.parquet.schema2.annotate_schema2_parquet import cli, produce_regions
from dae.parquet.schema2.loader import ParquetLoader
from dae.testing import (
    denovo_study,
    setup_denovo,
    setup_directories,
    setup_pedigree,
    setup_vcf,
    vcf_study,
)
from dae.testing.t4c8_import import t4c8_gpf


@pytest.fixture
def t4c8_instance(tmp_path: pathlib.Path) -> GPFInstance:
    root_path = tmp_path
    setup_directories(
        root_path,
        {
            "grr.yaml": textwrap.dedent(f"""
                id: t4c8_local
                type: directory
                directory: {root_path!s}
            """),
            "new_annotation.yaml": textwrap.dedent("""
                - position_score:
                    resource_id: three
                    attributes:
                    - source: score_three
                      name: score_A
                    - source: score_three
                      name: score_A_internal
                      internal: true
            """),
            "new_annotation_2.yaml": textwrap.dedent("""
                - position_score:
                    resource_id: three
                    attributes:
                    - source: score_three
                      name: score_A
                    - source: score_three
                      name: score_A_internal
                      internal: true
                - position_score: two
            """),
            "one": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_one
                          type: float
                          name: score
                """),
            },
            "two": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_two
                          type: float
                          name: score
                """),
            },
            "three": {
                "genomic_resource.yaml": textwrap.dedent("""
                        type: position_score
                        table:
                            filename: data.txt
                        scores:
                        - id: score_three
                          type: float
                          name: score
                """),
            },
        },
    )
    one_content = textwrap.dedent("""
        chrom  pos_begin  score
        chr1   4          0.01
        chr1   54         0.02
        chr1   90         0.03
        chr1   100        0.04
        chr1   119        0.05
        chr1   122        0.06
    """)
    two_content = textwrap.dedent("""
        chrom  pos_begin  score
        chr1   4          0.11
        chr1   54         0.12
        chr1   90         0.13
        chr1   100        0.14
        chr1   119        0.15
        chr1   122        0.16
    """)
    three_content = textwrap.dedent("""
        chrom  pos_begin  score
        chr1   4          0.21
        chr1   54         0.22
        chr1   90         0.23
        chr1   100        0.24
        chr1   119        0.25
        chr1   122        0.26
    """)
    setup_denovo(root_path / "one" / "data.txt", one_content)
    setup_denovo(root_path / "two" / "data.txt", two_content)
    setup_denovo(root_path / "three" / "data.txt", three_content)
    return t4c8_gpf(root_path)


@pytest.fixture
def t4c8_study_pedigree() -> str:
    return textwrap.dedent("""
        familyId personId dadId momId sex status role
        f1.1     mom1     0     0     2   1      mom
        f1.1     dad1     0     0     1   1      dad
        f1.1     ch1      dad1  mom1  2   2      prb
        f1.3     mom3     0     0     2   1      mom
        f1.3     dad3     0     0     1   1      dad
        f1.3     ch3      dad3  mom3  2   2      prb
    """)


@pytest.fixture
def t4c8_study_variants() -> str:
    return textwrap.dedent("""
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##contig=<ID=chr1>
    ##contig=<ID=chr2>
    ##contig=<ID=chr3>
    #CHROM POS  ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1 mom3 dad3 ch3
    chr1   4    .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/1  0/2  0/2
    chr1   54   .  T   C    .    .      .    GT     0/1  0/0  0/1 0/0  0/0  0/0
    chr1   90   .  G   C,GA .    .      .    GT     0/1  0/2  0/2 0/1  0/2  0/1
    chr1   100  .  T   G,TA .    .      .    GT     0/1  0/1  0/0 0/2  0/2  0/0
    chr1   119  .  A   G,C  .    .      .    GT     0/0  0/2  0/2 0/1  0/2  0/1
    chr1   122  .  A   C,AC .    .      .    GT     0/1  0/1  0/1 0/2  0/2  0/2
    """)


@pytest.fixture
def t4c8_study_variants_denovo() -> str:
    return textwrap.dedent("""
    chrom  position   ref   alt   family_id  genotype
    chr1   4          T     G,TA  f1.1       0/1,0/1,0/0
    chr1   54         T     C     f1.1       0/1,0/0,0/1
    chr1   90         G     C,GA  f1.1       0/1,0/2,0/2
    chr1   100        T     G,TA  f1.1       0/1,0/1,0/0
    chr1   119        A     G,C   f1.1       0/0,0/2,0/2
    chr1   122        A     C,AC  f1.1       0/1,0/1,0/1
    chr1   4          T     G,TA  f3.1       0/1,0/2,0/2
    chr1   54         T     C     f3.1       0/0,0/0,0/0
    chr1   90         G     C,GA  f3.1       0/1,0/2,0/1
    chr1   100        T     G,TA  f3.1       0/2,0/2,0/0
    chr1   119        A     G,C   f3.1       0/1,0/2,0/1
    chr1   122        A     C,AC  f3.1       0/2,0/2,0/2
    """)


@pytest.fixture
def t4c8_project_config() -> dict:
    return {
        "destination": {"storage_type": "schema2"},
        "annotation": [
            {"position_score": {
                "resource_id": "one",
                "attributes": [{
                    "source": "score_one",
                    "name": "score_A",
                }],
            }},
            {"position_score": "two"},
        ],
    }


@pytest.fixture
def t4c8_study_nonpartitioned(
    t4c8_instance: GPFInstance,
    t4c8_study_pedigree: str,
    t4c8_study_variants: str,
    t4c8_project_config: dict,
) -> str:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_nonpartitioned" / "pedigree" / "in.ped",
        t4c8_study_pedigree,
    )
    vcf_path = setup_vcf(
        root_path / "study_nonpartitioned" / "vcf" / "in.vcf.gz",
        t4c8_study_variants,
    )
    vcf_study(
        root_path, "study_nonpartitioned",
        ped_path, [vcf_path],
        t4c8_instance,
        project_config_overwrite=t4c8_project_config,
    )
    return f"{root_path}/work_dir/study_nonpartitioned"


@pytest.fixture
def t4c8_study_partitioned(
    t4c8_instance: GPFInstance,
    t4c8_study_pedigree: str,
    t4c8_study_variants: str,
    t4c8_project_config: dict,
) -> str:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_partitioned" / "pedigree" / "in.ped",
        t4c8_study_pedigree,
    )
    vcf_path = setup_vcf(
        root_path / "study_partitioned" / "vcf" / "in.vcf.gz",
        t4c8_study_variants,
    )

    project_config_update = {
        "partition_description": {
            "region_bin": {
                "chromosomes": ["chr1"],
                "region_length": 100,
            },
            "frequency_bin": {
                "rare_boundary": 25.0,
            },
            "coding_bin": {
                "coding_effect_types": [
                    "frame-shift",
                    "noStart",
                    "missense",
                    "synonymous",
                ],
            },
            "family_bin": {
                "family_bin_size": 2,
            },
        },
    }
    vcf_study(
        root_path, "study_partitioned",
        ped_path, [vcf_path],
        t4c8_instance,
        project_config_update=project_config_update,
        project_config_overwrite=t4c8_project_config,
    )
    return f"{root_path}/work_dir/study_partitioned"


@pytest.fixture
def t4c8_annotationless_study(
    t4c8_instance: GPFInstance,
    t4c8_study_pedigree: str,
    t4c8_study_variants: str,
) -> str:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "annotationless_study" / "pedigree" / "in.ped",
        t4c8_study_pedigree,
    )
    vcf_path = setup_vcf(
        root_path / "annotationless_study" / "vcf" / "in.vcf.gz",
        t4c8_study_variants,
    )
    vcf_study(
        root_path, "annotationless_study",
        ped_path, [vcf_path],
        t4c8_instance,
        project_config_overwrite={
            "destination": {"storage_type": "schema2"},
            "annotation": [],
        },
    )
    return f"{root_path}/work_dir/annotationless_study"


@pytest.fixture
def t4c8_study_denovo(
    t4c8_instance: GPFInstance,
    t4c8_study_pedigree: str,
    t4c8_study_variants_denovo: str,
    t4c8_project_config: dict,
) -> str:
    root_path = pathlib.Path(t4c8_instance.dae_dir)
    ped_path = setup_pedigree(
        root_path / "study_denovo" / "pedigree" / "in.ped",
        t4c8_study_pedigree,
    )
    dnv_path = setup_denovo(
        root_path / "study_denovo" / "denovo" / "variants.tsv",
        t4c8_study_variants_denovo,
    )

    config_update = {
        "input": {
            "denovo": {
                "chrom": "chrom",
                "pos": "position",
                "ref": "ref",
                "alt": "alt",
                "family_id": "family_id",
                "genotype": "genotype",
            },
        },
    }

    denovo_study(
        root_path, "study_denovo",
        ped_path, [dnv_path],
        t4c8_instance,
        project_config_update=config_update,
        project_config_overwrite=t4c8_project_config,
    )
    return f"{root_path}/work_dir/study_denovo"


@pytest.fixture(params=["nonpartitioned", "partitioned",
                        "annotationless", "denovo"])
def study(
    t4c8_study_nonpartitioned: str,
    t4c8_study_partitioned: str,
    t4c8_annotationless_study: str,
    t4c8_study_denovo: str,
    request: pytest.FixtureRequest,
) -> str:
    if request.param == "nonpartitioned":
        return t4c8_study_nonpartitioned
    if request.param == "partitioned":
        return t4c8_study_partitioned
    if request.param == "denovo":
        return t4c8_study_denovo
    return t4c8_annotationless_study


def test_reannotate_parquet_metadata(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    output_dir = str(tmp_path / "out")
    work_dir = str(tmp_path / "work")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        study, annotation_file_new,
        "-o", output_dir,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
    ])

    loader_result = ParquetLoader.load_from_dir(output_dir)

    result_pipeline = dict(loader_result.meta).pop("annotation_pipeline")

    expected_pipeline = textwrap.dedent(textwrap.dedent("""
        - position_score:
            resource_id: three
            attributes:
            - source: score_three
              name: score_A
            - source: score_three
              name: score_A_internal
              internal: true
        """))[1:]
    assert result_pipeline == expected_pipeline


def test_reannotate_parquet_symlinking(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    output_dir = str(tmp_path / "out")
    work_dir = str(tmp_path / "work")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        study, annotation_file_new,
        "-o", output_dir,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
    ])

    loader_old = ParquetLoader.load_from_dir(study)
    loader_result = ParquetLoader.load_from_dir(output_dir)

    # check pedigree is symlinked
    pedigree_path = pathlib.Path(loader_result.layout.pedigree)
    assert pedigree_path.parent.is_symlink()
    assert pedigree_path.parent.exists()
    assert pedigree_path.samefile(loader_old.layout.pedigree)

    # check family variants are symlinked
    assert loader_result.layout.family is not None
    assert loader_old.layout.family is not None
    family_vs_path = pathlib.Path(loader_result.layout.family)
    assert family_vs_path.is_symlink()
    assert family_vs_path.exists()
    assert family_vs_path.samefile(loader_old.layout.family)


def test_reannotate_parquet_symlinking_relative(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    output_dir = str(tmp_path / "out")
    work_dir = str(tmp_path / "work")

    # Use relative path instead of absolute
    input_dir_parent = pathlib.Path(study).parent.absolute()
    study = str(pathlib.Path(study).relative_to(input_dir_parent))
    monkeypatch.chdir(input_dir_parent)

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        study, annotation_file_new,
        "-o", output_dir,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
    ])

    loader_old = ParquetLoader.load_from_dir(study)
    loader_result = ParquetLoader.load_from_dir(output_dir)

    # check pedigree is symlinked
    pedigree_path = pathlib.Path(loader_result.layout.pedigree)
    assert pedigree_path.parent.is_symlink()
    assert pedigree_path.parent.exists()
    assert pedigree_path.samefile(loader_old.layout.pedigree)

    # check family variants are symlinked
    assert loader_result.layout.family is not None
    assert loader_old.layout.family is not None
    family_vs_path = pathlib.Path(loader_result.layout.family)
    assert family_vs_path.is_symlink()
    assert family_vs_path.exists()
    assert family_vs_path.samefile(loader_old.layout.family)


def test_reannotate_parquet_variants(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    output_dir = str(tmp_path / "out")
    work_dir = str(tmp_path / "work")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        study, annotation_file_new,
        "-o", output_dir,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
    ])

    loader_result = ParquetLoader.load_from_dir(output_dir)

    # check variants are correctly reannotated
    result = set()
    for sv in loader_result.fetch_summary_variants():
        assert not sv.has_attribute("score_two")
        assert sv.has_attribute("score_A")
        result.add(sv.get_attribute("score_A").pop())
    assert sorted(result) == pytest.approx(
        [0.21, 0.22, 0.23, 0.24, 0.25, 0.26], rel=1e-3)


def test_reannotate_parquet_merging(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    output_dir = tmp_path / "out"
    work_dir = str(tmp_path / "work")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        study, annotation_file_new,
        "-o", str(output_dir),
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
        "--region-size", "25",
    ])

    expected_pq_files = 5 if "study_partitioned" in study else 1

    # check only merged parquet files are left
    parquets_glob = str(output_dir / "summary" / "**" / "*.parquet")
    assert len(glob(parquets_glob, recursive=True)) == expected_pq_files

    # check all variants present
    loader_result = ParquetLoader.load_from_dir(str(output_dir))
    assert len(list(loader_result.fetch_summary_variants())) == 6


def test_internal_attributes_reannotation(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    output_dir = str(tmp_path / "out")
    work_dir = str(tmp_path / "work")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        study, annotation_file_new,
        "-o", output_dir,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
    ])

    # check internal attributes are not saved
    for sv in ParquetLoader.load_from_dir(output_dir).fetch_summary_variants():
        assert not sv.has_attribute("score_A_internal")


def test_annotationless_study_autodetection(
    mocker: pytest_mock.MockerFixture,
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    t4c8_annotationless_study: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    output_dir = str(tmp_path / "out")
    work_dir = str(tmp_path / "work")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    mocker.spy(ReannotationPipeline, "__init__")

    cli([
        t4c8_annotationless_study, annotation_file_new,
        "-o", output_dir,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
    ])

    # check auto-detection by asserting
    # reannotation pipeline is NOT constructed
    assert ReannotationPipeline.__init__.call_count == 0  # type: ignore


def test_autodetection_reannotate(
    mocker: pytest_mock.MockerFixture,
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    t4c8_study_nonpartitioned: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    output_dir = str(tmp_path / "out")
    work_dir = str(tmp_path / "work")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    mocker.spy(ReannotationPipeline, "__init__")

    cli([
        t4c8_study_nonpartitioned, annotation_file_new,
        "-o", output_dir,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
    ])

    # check auto-detection by asserting reannotation pipeline is constructed
    assert ReannotationPipeline.__init__.call_count >= 1  # type: ignore


def test_reannotate_in_place(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    work_dir = str(tmp_path / "work")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        study, annotation_file_new,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
        "--in-place",
    ])

    date = datetime.today().strftime("%Y%m%d")

    assert pathlib.Path(study, "summary").exists()  # new
    assert pathlib.Path(study, f"summary_{date}").exists()  # backup

    assert pathlib.Path(study, "meta", "meta.parquet").exists()  # new
    assert pathlib.Path(
        study, "meta", f"meta_{date}.parquet").exists()  # backup

    # check variants are correctly reannotated
    loader = ParquetLoader.load_from_dir(study)
    vs = list(loader.fetch_summary_variants())
    assert len(vs) == 6
    result = set()
    for sv in vs:
        assert not sv.has_attribute("score_two")
        assert sv.has_attribute("score_A")
        result.add(sv.get_attribute("score_A").pop())
    assert sorted(result) == pytest.approx(
        [0.21, 0.22, 0.23, 0.24, 0.25, 0.26], rel=1e-3)


def test_reannotate_in_place_increment_backup_filenames(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    work_dir = str(tmp_path / "work")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    times = 5

    for _ in range(times):
        cli([
            study, annotation_file_new,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", "1",
            "--in-place",
        ])

    date = datetime.today().strftime("%Y%m%d")

    assert pathlib.Path(study, "summary").exists()
    for i in range(times - 1):
        assert pathlib.Path(study, f"summary_{date}-{i + 1}").exists()

    assert pathlib.Path(study, "meta", "meta.parquet").exists()
    for i in range(times - 1):
        assert pathlib.Path(
            study, "meta", f"meta_{date}-{i + 1}.parquet").exists()


def test_print_meta(
    t4c8_instance: GPFInstance,
    t4c8_study_partitioned: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    gpf_instance_genomic_context_fixture(t4c8_instance)
    buf = io.StringIO()
    with redirect_stdout(buf):
        cli([t4c8_study_partitioned, "--meta"])
    res = buf.getvalue()
    assert res
    assert "partition_description" in res
    assert "annotation_pipeline" in res
    assert "summary_schema" in res
    assert "family_schema" in res


def test_output_argument_behaviour(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    t4c8_study_nonpartitioned: str,
    gpf_instance_genomic_context_fixture:
        Callable[[GPFInstance], GenomicContext],
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    work_dir = str(tmp_path / "work")
    output_dir = str(tmp_path / "out")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli_args = [
        t4c8_study_nonpartitioned,
        annotation_file_new,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
    ]

    with pytest.raises(ValueError, match="No output path was provided!"):
        cli(cli_args)

    cli([*cli_args, "-o", output_dir, "--force"])
    vs = list(ParquetLoader.load_from_dir(output_dir).fetch_summary_variants())
    assert len(vs) == 6


def test_region_option(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    output_dir = str(tmp_path / "out")
    work_dir = str(tmp_path / "work")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        study, annotation_file_new,
        "-o", output_dir,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
        "--region", "chr1:90-100",
    ])

    loader_result = ParquetLoader.load_from_dir(output_dir)

    result = set()
    for sv in loader_result.fetch_summary_variants():
        assert not sv.has_attribute("score_two")
        assert sv.has_attribute("score_A")
        result.add(sv.get_attribute("score_A").pop())
    assert sorted(result) == pytest.approx([0.23, 0.24], rel=1e-3)


def test_region_option_invalid(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    output_dir = str(tmp_path / "out")
    work_dir = str(tmp_path / "work")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    with pytest.raises(
        KeyError, match="No such contig 'chrX' found in data!",
    ):
        cli([
            study, annotation_file_new,
            "-o", output_dir,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", "1",
            "--region", "chrX:90-100",
        ])


def test_data_removal_func_preserves_other_files(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    t4c8_study_nonpartitioned: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    annotation_file_new = str(root_path / "new_annotation.yaml")
    grr_file = str(root_path / "grr.yaml")
    work_dir = str(tmp_path / "work")
    output_dir = tmp_path / "out"

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli_args = [
        t4c8_study_nonpartitioned,
        annotation_file_new,
        "-w", work_dir,
        "--grr", grr_file,
        "-j", "1",
        "-o", str(output_dir),
    ]

    cli(cli_args)

    some_file = output_dir / "some_random_file.txt"
    some_file.touch()
    some_dir = output_dir / "some_random_dir"
    some_dir.mkdir()

    assert some_file.exists()
    assert some_dir.exists()
    assert {path.name for path in output_dir.glob("*")} == {
        "meta", "summary", "family", "pedigree",  # schema2 dirs
        "some_random_file.txt", "some_random_dir",  # new stuff
    }

    cli([*cli_args, "--force"])

    assert some_file.exists()
    assert some_dir.exists()
    assert {path.name for path in output_dir.glob("*")} == {
        "meta", "summary", "family", "pedigree",  # schema2 dirs
        "some_random_file.txt", "some_random_dir",  # new stuff
    }


def test_full_reannotation_flag(
    mocker: pytest_mock.MockerFixture,
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    t4c8_study_nonpartitioned: str,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    grr_file = str(root_path / "grr.yaml")

    gpf_instance_genomic_context_fixture(t4c8_instance)

    out_path = str(tmp_path / "out")
    cli([t4c8_study_nonpartitioned,
         str(root_path / "new_annotation_2.yaml"),
         "--grr", grr_file,
         "-j", "1",
         "-o", out_path,
         "-w", str(tmp_path / "work")])

    mocker.spy(PositionScoreAnnotator, "annotate")

    out_path_2 = str(tmp_path / "out2")
    cli([out_path,
         str(root_path / "new_annotation.yaml"),
         "--grr", grr_file,
         "-j", "1",
         "--full-reannotation",
         "-o", out_path_2,
         "-w", str(tmp_path / "work2")])

    # due to --full-reannotation being passed, the position score annotator
    # should have re-annotated (even though it has not changed), indicated
    # by 11 calls to its annotate method
    assert PositionScoreAnnotator.annotate.call_count == 11  # type: ignore

    loader = ParquetLoader.load_from_dir(out_path_2)
    vs = list(loader.fetch_summary_variants())
    attrs = list(vs[0].alt_alleles[0].attributes.keys())

    # the difference between new_annotation_2.yaml and
    # new_annotation.yaml is that new_annotation_2.yaml also
    # annotates with the resource "two", while new_annotation.yaml doesn't
    # this is used to test that --full-reannotation will clear out attributes
    # from previous annotations properly
    assert "score_A" in attrs
    assert "score_two" not in attrs


@pytest.mark.parametrize(
    "region_size,target_region,expected",
    [
        (100, "chrZ:200-600",
         ["chrZ:200-200",
          "chrZ:201-300",
          "chrZ:301-400",
          "chrZ:401-500",
          "chrZ:501-600"]),

        (50, "chrZ:234-345",
         ["chrZ:234-250",
          "chrZ:251-300",
          "chrZ:301-345"]),

        (300, "chrZ:200-700",
         ["chrZ:200-300",
          "chrZ:301-600",
          "chrZ:601-700"]),

        (500, None,
         ["chrZ:1-500",
          "chrZ:501-1000",
          "chrW:1-500",
          "chrW:501-1000",
          "chrW:1001-1500",
          "chrW:1501-2000"]),

        (500, "chrZ:1-9999",
         ["chrZ:1-500",
          "chrZ:501-1000"]),

        (500, "chrZ:800-900",
         ["chrZ:800-900"]),

        (9999, None,
         ["chrZ:1-1000",
          "chrW:1-2000"]),
    ],
)
def test_produce_regions(
    region_size: int,
    target_region: str | None,
    expected: list[str],
) -> None:
    contig_lens = {"chrZ": 1000, "chrW": 2000}
    result = produce_regions(target_region, region_size, contig_lens)
    assert result == expected
