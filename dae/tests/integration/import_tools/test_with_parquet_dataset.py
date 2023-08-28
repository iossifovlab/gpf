# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib

import pytest

from dae.testing import setup_pedigree, setup_vcf, vcf_import
from dae.testing import alla_gpf
from dae.testing.import_helpers import StudyInputLayout
from dae.import_tools.cli import run_with_project
from dae.import_tools.import_tools import ImportProject
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture(scope="module")
def vcf_import_data(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage: GenotypeStorage
) -> tuple[pathlib.Path, GPFInstance, StudyInputLayout]:
    root_path = tmp_path_factory.mktemp(
        f"parquet_dataset_{genotype_storage.storage_id}")

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
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=chrA>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1
        chrA   1   .  A   C   .    .      .    GT     0/1 0/0 0/1
        chrA   2   .  A   G   .    .      .    GT     0/0 0/1 0/1
        """)

    return root_path, gpf_instance, StudyInputLayout(
        "with_parquet_dataset", ped_path, [vcf_path], [], [], [])


@pytest.fixture(scope="module")
def vcf_project_to_parquet(
    tmp_path_factory: pytest.TempPathFactory,
    vcf_import_data: tuple[pathlib.Path, GPFInstance, StudyInputLayout],
    genotype_storage: GenotypeStorage
) -> ImportProject:
    root_path, gpf_instance, layout = vcf_import_data

    project_config_overwrite = {
        "destination": {
            "storage_type": genotype_storage.get_storage_type()
        }
    }
    project = vcf_import(
        root_path,
        "parquet_dataset", layout.pedigree, layout.vcf,
        gpf_instance,
        project_config_overwrite=project_config_overwrite)
    return project


@pytest.fixture(scope="module")
def vcf_project_from_parquet(
    tmp_path_factory: pytest.TempPathFactory,
    vcf_import_data: tuple[pathlib.Path, GPFInstance, StudyInputLayout],
    genotype_storage: GenotypeStorage
) -> ImportProject:
    root_path, gpf_instance, layout = vcf_import_data

    project_config_update = {
        "processing_config": {
            "work_dir": str(root_path / "work_dir2"),
            "parquet_dataset_dir": str(
                root_path / "work_dir" / "parquet_dataset")
        }
    }
    project = vcf_import(
        root_path,
        "parquet_dataset", layout.pedigree, layout.vcf,
        gpf_instance,
        project_config_update=project_config_update)
    return project


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_impala2(reason="supported for schema2 impala")
@pytest.mark.gs_gcp(reason="supported for gcp")
def test_with_destination_storage_type(
    vcf_project_to_parquet: ImportProject,
    vcf_project_from_parquet: ImportProject,
    genotype_storage: GenotypeStorage
) -> None:

    run_with_project(vcf_project_to_parquet)
    assert os.path.exists(
        os.path.join(
            vcf_project_to_parquet.work_dir, "parquet_dataset", "pedigree",
            "pedigree.parquet"))

    run_with_project(vcf_project_from_parquet)

    gpf_instance = vcf_project_from_parquet.get_gpf_instance()
    gpf_instance.reload()
    study = gpf_instance.get_genotype_data("parquet_dataset")
    assert study is not None

    assert len(list(study.query_variants())) == 2
