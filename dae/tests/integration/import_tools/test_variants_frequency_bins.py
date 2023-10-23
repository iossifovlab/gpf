# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib

import pytest

from dae.testing import setup_pedigree, setup_vcf, vcf_study, \
    setup_denovo, denovo_import
from dae.testing import alla_gpf
from dae.testing.import_helpers import StudyInputLayout
from dae.import_tools.cli import run_with_project
from dae.import_tools.import_tools import ImportProject
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData


@pytest.fixture(scope="module")
def vcf_import_data(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage: GenotypeStorage
) -> tuple[pathlib.Path, GPFInstance, StudyInputLayout]:
    root_path = tmp_path_factory.mktemp("vcf_import")
    gpf_instance = alla_gpf(root_path)

    if genotype_storage:
        gpf_instance\
            .genotype_storages\
            .register_default_storage(genotype_storage)

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
##contig=<ID=chrA>
#CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
chrA   1   .  A   C   .    .      .    GT     0/1 0/1 0/1 0/0 0/0 0/1
chrA   2   .  A   G   .    .      .    GT     0/0 0/0 0/1 0/1 0/0 0/1
        """)

    return root_path, gpf_instance, StudyInputLayout(
        "with_parquet_dataset", ped_path, [vcf_path], [], [], [])


@pytest.fixture(scope="module")
def vcf_fixture(
    vcf_import_data: tuple[pathlib.Path, GPFInstance, StudyInputLayout],
    genotype_storage: GenotypeStorage
) -> tuple[pathlib.Path, GenotypeData]:
    root_path, gpf_instance, layout = vcf_import_data

    project_config_update = {
        "input": {
            "vcf": {
                "denovo_mode": "denovo"
            }
        },
        "destination": {
            "storage_id": genotype_storage.storage_id
        },
        "partition_description": {
            "frequency_bin": {
                "rare_boundary": 20.0
            }
        }
    }
    return root_path, vcf_study(
        root_path,
        "vcf_fixture", layout.pedigree,
        layout.vcf,
        gpf_instance,
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
    ]
)
def test_family_frequency_bin_for_vcf(
    vcf_fixture: tuple[pathlib.Path, GenotypeData],
    genotype_storage: GenotypeStorage,
    label: str, frequency_bin: int, exists: bool
) -> None:

    root_path, _ = vcf_fixture
    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            f"vcf_fixture/family/frequency_bin="
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
    ]
)
def test_summary_frequency_bin_for_vcf(
    vcf_fixture: tuple[pathlib.Path, GenotypeData],
    genotype_storage: GenotypeStorage,
    label: str, frequency_bin: int, exists: bool
) -> None:

    root_path, _ = vcf_fixture
    assert os.path.exists(
        os.path.join(
            root_path / "work_dir",
            f"vcf_fixture/summary/frequency_bin="
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
    ]
)
def test_frequency_bin_queries(
    frequency_filter: list[tuple], count: int,
    vcf_fixture: tuple[pathlib.Path, GenotypeData],
    genotype_storage: GenotypeStorage,
) -> None:
    _, study = vcf_fixture
    vs = list(study.query_variants(frequency_filter=frequency_filter))
    assert len(vs) == count


@pytest.fixture(scope="module")
def denovo_import_data(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage: GenotypeStorage
) -> tuple[pathlib.Path, GPFInstance, StudyInputLayout]:
    root_path = tmp_path_factory.mktemp(
        f"denovo_dataset_{genotype_storage.storage_id}")

    gpf_instance = alla_gpf(root_path)

    if genotype_storage:
        gpf_instance\
            .genotype_storages\
            .register_default_storage(genotype_storage)

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
        familyId location variant   bestState
        f1       chrA:1   sub(A->C) 2||2||1/0||0||1
        f2       chrA:2   sub(A->C) 2||2||1/0||0||1
        """)

    return root_path, gpf_instance, StudyInputLayout(
        "with_parquet_dataset", ped_path, [], [denovo_path], [], [])


@pytest.fixture(scope="module")
def denovo_project_to_parquet(
    tmp_path_factory: pytest.TempPathFactory,
    denovo_import_data: tuple[pathlib.Path, GPFInstance, StudyInputLayout],
    genotype_storage: GenotypeStorage
) -> ImportProject:
    root_path, gpf_instance, layout = denovo_import_data

    project_config_update = {
        "destination": {
            "storage_type": genotype_storage.get_storage_type()
        },
        "partition_description": {
            "frequency_bin": {
                "rare_boundary": 50.0
            }
        }
    }
    project = denovo_import(
        root_path,
        "parquet_dataset", layout.pedigree, layout.denovo,
        gpf_instance,
        project_config_update=project_config_update)
    return project


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
    ]
)
def test_denovo_frequency_bin_for_denovo_import(
    denovo_project_to_parquet: ImportProject,
    genotype_storage: GenotypeStorage,
    label: str, frequency_bin: int, exists: bool
) -> None:

    run_with_project(denovo_project_to_parquet)
    assert os.path.exists(
        os.path.join(
            denovo_project_to_parquet.work_dir,
            f"parquet_dataset/family/frequency_bin="
            f"{frequency_bin}")) == exists, label
