import pathlib
import textwrap
import pytest
from glob import glob

from dae.gpf_instance import GPFInstance
from dae.variants_loaders.parquet.loader import ParquetLoader
from dae.testing import setup_pedigree, setup_vcf, setup_directories, \
    setup_denovo, vcf_study
from dae.testing.t4c8_import import t4c8_gpf

from dae.annotation.annotate_schema2_parquet import cli


@pytest.fixture
def t4c8_instance(tmp_path: pathlib.Path) -> GPFInstance:
    root_path = tmp_path
    setup_directories(
        root_path,
        {
            "grr.yaml": textwrap.dedent(f"""
                id: t4c8_local
                type: directory
                directory: {str(root_path)}
            """),
            "new_annotation.yaml": textwrap.dedent("""
                - position_score:
                    resource_id: three
                    attributes:
                    - source: score_three
                      name: score_A
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
                """)
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
                """)
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
                """)
            }
        }
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
    gpf_instance = t4c8_gpf(root_path)
    return gpf_instance


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
def t4c8_project_config() -> dict:
    return {
        "destination": {"storage_type": "schema2"},
        "annotation": [
            {"position_score": {
                "resource_id": "one",
                "attributes": [{
                    "source": "score_one",
                    "name": "score_A",
                }]
            }},
            {"position_score": "two"}
        ]
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
        t4c8_study_pedigree
    )
    vcf_path = setup_vcf(
        root_path / "study_nonpartitioned" / "vcf" / "in.vcf.gz",
        t4c8_study_variants
    )
    vcf_study(
        root_path, "study_nonpartitioned",
        ped_path, [vcf_path],
        t4c8_instance,
        project_config_overwrite=t4c8_project_config
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
        t4c8_study_pedigree
    )
    vcf_path = setup_vcf(
        root_path / "study_partitioned" / "vcf" / "in.vcf.gz",
        t4c8_study_variants
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
                ]
            },
            "family_bin": {
                "family_bin_size": 2,
            }
        },
    }
    vcf_study(
        root_path, "study_partitioned",
        ped_path, [vcf_path],
        t4c8_instance,
        project_config_update=project_config_update,
        project_config_overwrite=t4c8_project_config
    )
    return f"{root_path}/work_dir/study_partitioned"


@pytest.mark.parametrize("study", [("t4c8_study_nonpartitioned"),
                                   ("t4c8_study_partitioned")])
def test_reannotate_parquet_metadata(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    t4c8_study_nonpartitioned,
    t4c8_study_partitioned,
    gpf_instance_genomic_context_fixture
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    input_dir = t4c8_study_nonpartitioned \
        if study == "t4c8_study_nonpartitioned" \
        else t4c8_study_partitioned
    annotation_file_new = root_path / "new_annotation.yaml"
    grr_file = root_path / "grr.yaml"
    output_dir = tmp_path / "out"
    work_dir = tmp_path / "work"

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        str(a) for a in [
            input_dir, annotation_file_new,
            "-o", output_dir,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", 1
        ]
    ])

    loader_old = ParquetLoader(input_dir)
    loader_result = ParquetLoader(output_dir)

    # check metadata is correctly updated
    expected_meta = dict(loader_old.meta)
    expected_meta["annotation_pipeline"] = textwrap.dedent("""
        - position_score:
            resource_id: three
            attributes:
            - source: score_three
              name: score_A
    """)
    assert loader_result.meta == expected_meta


@pytest.mark.parametrize("study", [("t4c8_study_nonpartitioned"),
                                   ("t4c8_study_partitioned")])
def test_reannotate_parquet_symlinking(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    t4c8_study_nonpartitioned,
    t4c8_study_partitioned,
    gpf_instance_genomic_context_fixture
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    input_dir = t4c8_study_nonpartitioned \
        if study == "t4c8_study_nonpartitioned" \
        else t4c8_study_partitioned
    annotation_file_new = root_path / "new_annotation.yaml"
    grr_file = root_path / "grr.yaml"
    output_dir = tmp_path / "out"
    work_dir = tmp_path / "work"

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        str(a) for a in [
            input_dir, annotation_file_new,
            "-o", output_dir,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", 1
        ]
    ])

    loader_old = ParquetLoader(input_dir)
    loader_result = ParquetLoader(output_dir)

    # check pedigree is symlinked
    pedigree_path = pathlib.Path(loader_result.layout.pedigree)
    assert pedigree_path.parent.is_symlink()
    assert pedigree_path.samefile(loader_old.layout.pedigree)

    # check family variants are symlinked
    family_vs_path = pathlib.Path(loader_result.layout.family)
    assert family_vs_path.is_symlink()
    assert family_vs_path.samefile(loader_old.layout.family)


@pytest.mark.parametrize("study", [("t4c8_study_nonpartitioned"),
                                   ("t4c8_study_partitioned")])
def test_reannotate_parquet_variants(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    t4c8_study_nonpartitioned,
    t4c8_study_partitioned,
    gpf_instance_genomic_context_fixture
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    input_dir = t4c8_study_nonpartitioned \
        if study == "t4c8_study_nonpartitioned" \
        else t4c8_study_partitioned
    annotation_file_new = root_path / "new_annotation.yaml"
    grr_file = root_path / "grr.yaml"
    output_dir = tmp_path / "out"
    work_dir = tmp_path / "work"

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        str(a) for a in [
            input_dir, annotation_file_new,
            "-o", output_dir,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", 1
        ]
    ])

    loader_result = ParquetLoader(output_dir)

    # check variants are correctly reannotated 
    result = set()
    for sv in loader_result.fetch_summary_variants():
        assert not sv.has_attribute("score_two")
        assert sv.has_attribute("score_A")
        result.add(sv.get_attribute("score_A").pop())
    assert result == {0.21, 0.22, 0.23, 0.24, 0.25, 0.26}


@pytest.mark.parametrize("study", [("t4c8_study_nonpartitioned"),
                                   ("t4c8_study_partitioned")])
def test_reannotate_parquet_merging(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
    study: str,
    t4c8_study_nonpartitioned,
    t4c8_study_partitioned,
    gpf_instance_genomic_context_fixture,
) -> None:
    root_path = pathlib.Path(t4c8_instance.dae_dir) / ".."
    input_dir = t4c8_study_nonpartitioned \
        if study == "t4c8_study_nonpartitioned" \
        else t4c8_study_partitioned
    annotation_file_new = root_path / "new_annotation.yaml"
    grr_file = root_path / "grr.yaml"
    output_dir = tmp_path / "out"
    work_dir = tmp_path / "work"

    gpf_instance_genomic_context_fixture(t4c8_instance)

    cli([
        str(a) for a in [
            input_dir, annotation_file_new,
            "-o", output_dir,
            "-w", work_dir,
            "--grr", grr_file,
            "-j", 1,
            "--region-size", 25,
        ]
    ])

    expected_pq_files = 5 if study == "t4c8_study_partitioned" \
                          else 1

    # check only merged parquet files are left
    parquets_glob = str(output_dir / "summary" / "**" / "*.parquet")
    assert len(glob(parquets_glob, recursive=True)) == expected_pq_files

    # check all variants present
    loader_result = ParquetLoader(output_dir)
    assert len(list(loader_result.fetch_summary_variants())) == 6