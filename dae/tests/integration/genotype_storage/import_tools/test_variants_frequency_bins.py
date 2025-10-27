# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
from collections.abc import Callable

import pytest
from dae.genomic_resources.testing import (
    setup_denovo,
    setup_pedigree,
    setup_vcf,
)
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.cli import run_with_project
from dae.import_tools.import_tools import ImportProject
from dae.studies.study import GenotypeData
from dae.testing.alla_import import alla_gpf
from dae.testing.import_helpers import (
    StudyInputLayout,
    denovo_import,
    vcf_study,
)


@pytest.fixture
def vcf_import_data(
    tmp_path: pathlib.Path,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> tuple[pathlib.Path, GPFInstance, GenotypeStorage, StudyInputLayout]:
    root_path = tmp_path
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = alla_gpf(root_path, genotype_storage)

    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
chr1   1   .  A   C   .    .      .    GT     0/1 0/1 0/1 0/0 0/0 0/1
chr1   2   .  A   G   .    .      .    GT     0/0 0/0 0/1 0/1 0/0 0/1
        """)

    return (
        root_path, gpf_instance, genotype_storage,
        StudyInputLayout("vcf_fixture", ped_path, [vcf_path], [], [], []))


@pytest.fixture
def vcf_fixture(
    vcf_import_data: tuple[
        pathlib.Path, GPFInstance, GenotypeStorage, StudyInputLayout],
) -> tuple[pathlib.Path, GenotypeData]:
    root_path, gpf_instance, genotype_storage, layout = vcf_import_data

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo",
            },
        },
        "destination": {
            "storage_id": genotype_storage.storage_id,
        },
        "processing_config": {
            "include_reference": True,
        },
        "partition_description": {
            "frequency_bin": {
                "rare_boundary": 20.0,
            },
        },
    }
    return root_path, vcf_study(
        root_path,
        "vcf_frequency_bin", layout.pedigree,
        layout.vcf,
        gpf_instance=gpf_instance,
        project_config_update=project_config_update)


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_impala2(reason="supported for schema2 impala")
@pytest.mark.gs_gcp(reason="supported for gcp")
@pytest.mark.parametrize(
    "label,frequency_bin,exists",
    [
        ("denovo", 0, True),
        ("ultra rare", 1, True),
        ("rare <= 50%", 2, False),
        ("common >50", 3, True),
    ],
)
def test_family_frequency_bin_for_vcf(
    vcf_fixture: tuple[pathlib.Path, GenotypeData],
    label: str, frequency_bin: int,
    exists: bool,  # noqa: FBT001
) -> None:

    root_path, _ = vcf_fixture
    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            f"vcf_frequency_bin/family/frequency_bin="
            f"{frequency_bin}")) == exists, label


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_impala2(reason="supported for schema2 impala")
@pytest.mark.gs_gcp(reason="supported for gcp")
@pytest.mark.parametrize(
    "label,frequency_bin,exists",
    [
        ("denovo", 0, True),
        ("ultra rare", 1, False),
        ("rare <= 50%", 2, False),
        ("common >50", 3, True),
    ],
)
def test_summary_frequency_bin_for_vcf(
    vcf_fixture: tuple[pathlib.Path, GenotypeData],
    label: str,
    frequency_bin: int,
    exists: bool,  # noqa: FBT001
) -> None:

    root_path, _ = vcf_fixture
    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            f"vcf_frequency_bin/summary/frequency_bin="
            f"{frequency_bin}")) == exists, label


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_impala2(reason="supported for schema2 impala")
@pytest.mark.gs_gcp(reason="supported for gcp")
@pytest.mark.parametrize(
    "frequency_filter,count",
    [
        (None, 4),
        ([("af_allele_freq", (0.0, 20.0))], 2),
        ([("af_allele_freq", (20.0, 100.0))], 2),
    ],
)
def test_frequency_bin_queries(
    frequency_filter: list[tuple], count: int,
    vcf_fixture: tuple[pathlib.Path, GenotypeData],
) -> None:
    _, study = vcf_fixture
    vs = list(study.query_variants(frequency_filter=frequency_filter))
    assert len(vs) == count


@pytest.fixture
def denovo_import_data(
    tmp_path: pathlib.Path,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> tuple[pathlib.Path, GPFInstance, GenotypeStorage, StudyInputLayout]:
    root_path = tmp_path
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = alla_gpf(root_path, genotype_storage)

    ped_path = setup_pedigree(
        root_path / "denovo_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   2      prb
        """)
    denovo_path = setup_denovo(
        root_path / "denovo_data" / "in.tsv",
        """
        chrom  pos  ref  alt  person_id
        chr1   1    A    C    p1
        chr1   2    A    G    p2
        """)

    return (
        root_path, gpf_instance, genotype_storage,
        StudyInputLayout(
            "denovo_fixture", ped_path, [], [denovo_path], [], []))


@pytest.fixture
def denovo_project_to_parquet(
    denovo_import_data: tuple[
        pathlib.Path, GPFInstance, GenotypeStorage, StudyInputLayout],
) -> ImportProject:
    root_path, gpf_instance, genotype_storage, layout = denovo_import_data

    project_config_update = {
        "destination": {
            "storage_type": genotype_storage.storage_type,
        },
        "partition_description": {
            "frequency_bin": {
                "rare_boundary": 50.0,
            },
        },
    }
    return denovo_import(
        root_path,
        "denovo_frequency_bin", layout.pedigree, layout.denovo,
        gpf_instance=gpf_instance,
        project_config_update=project_config_update)


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_impala2(reason="supported for schema2 impala")
@pytest.mark.gs_gcp(reason="supported for gcp")
@pytest.mark.parametrize(
    "label,frequency_bin,exists",
    [
        ("denovo", 0, True),
        ("ultra rare", 1, False),
        ("rare <= 50%", 2, False),
        ("common >50", 3, False),
    ],
)
def test_denovo_frequency_bin_for_denovo_import(
    denovo_project_to_parquet: ImportProject,
    label: str,
    frequency_bin: int,
    exists: bool,  # noqa: FBT001
) -> None:

    run_with_project(denovo_project_to_parquet)
    assert os.path.exists(
        os.path.join(
            denovo_project_to_parquet.work_dir,
            f"denovo_frequency_bin/family/frequency_bin="
            f"{frequency_bin}")) == exists, label
