# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
from collections.abc import Callable

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.cli import run_with_project
from dae.import_tools.import_tools import ImportProject
from dae.testing import alla_gpf, setup_pedigree, setup_vcf, vcf_import
from dae.testing.import_helpers import StudyInputLayout


@pytest.fixture(scope="module")
def vcf_import_data(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> tuple[pathlib.Path, GPFInstance, GenotypeStorage, StudyInputLayout]:
    root_path = tmp_path_factory.mktemp("test_with_parquet_dataset")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = alla_gpf(root_path, genotype_storage)

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

    return (
        root_path, gpf_instance, genotype_storage,
        StudyInputLayout(
            "with_parquet_dataset", ped_path, [vcf_path], [], [], []))


@pytest.fixture(scope="module")
def vcf_project_to_parquet(
    vcf_import_data: tuple[
        pathlib.Path, GPFInstance, GenotypeStorage, StudyInputLayout],
) -> ImportProject:
    root_path, gpf_instance, genotype_storage, layout = vcf_import_data

    project_config_overwrite = {
        "destination": {
            "storage_type": genotype_storage.storage_type,
        },
    }
    return vcf_import(
        root_path,
        "parquet_dataset", layout.pedigree, layout.vcf,
        gpf_instance,
        project_config_overwrite=project_config_overwrite)


@pytest.fixture(scope="module")
def vcf_project_from_parquet(
    vcf_import_data: tuple[
        pathlib.Path, GPFInstance, GenotypeStorage, StudyInputLayout],
) -> ImportProject:
    root_path, gpf_instance, _genotype_storage, layout = vcf_import_data

    project_config_replace = {
        "id": "from_parquet_dataset",
        "processing_config": {
            "parquet_dataset_dir": str(
                root_path / "work_dir" / "parquet_dataset"),
        },
    }
    return vcf_import(
        root_path,
        "from_parquet_dataset", layout.pedigree, layout.vcf,
        gpf_instance,
        project_config_replace=project_config_replace)


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_impala2(reason="supported for schema2 impala")
@pytest.mark.gs_gcp(reason="supported for gcp")
def test_with_destination_storage_type(
    vcf_project_to_parquet: ImportProject,
    vcf_project_from_parquet: ImportProject,
) -> None:

    run_with_project(vcf_project_to_parquet)
    assert os.path.exists(
        os.path.join(
            vcf_project_to_parquet.work_dir, "parquet_dataset", "pedigree",
            "pedigree.parquet"))

    run_with_project(vcf_project_from_parquet)

    gpf_instance = vcf_project_from_parquet.get_gpf_instance()
    gpf_instance.reload()
    study = gpf_instance.get_genotype_data("from_parquet_dataset")
    assert study is not None

    assert len(list(study.query_variants())) == 2
