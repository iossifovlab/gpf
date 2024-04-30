# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
from dae.testing.import_helpers import StudyInputLayout, pedigree_import
from dae.testing import alla_gpf, setup_pedigree
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.cli import run_with_project
from dae.import_tools.import_tools import ImportProject

@pytest.fixture(scope="module")
def pedigree_only_import_data(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage: GenotypeStorage,
) -> tuple[pathlib.Path, GPFInstance, StudyInputLayout]:
    root_path = tmp_path_factory.mktemp(
        f"pedigree_dataset_{genotype_storage.storage_id}")

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

    return root_path, gpf_instance, StudyInputLayout(
        "pedigree_dataset", ped_path, [], [], [], [])

@pytest.fixture(scope="module")
def pedigree_only_project(
    tmp_path_factory: pytest.TempPathFactory,
    pedigree_only_import_data: tuple[pathlib.Path, GPFInstance, StudyInputLayout],
    genotype_storage: GenotypeStorage,
) -> ImportProject:
    root_path, gpf_instance, layout = pedigree_only_import_data

    project = pedigree_import(
        root_path,
        "pedigree_dataset", layout.pedigree,
        gpf_instance,
    )
    return project

def test_pedigree_only_import(
    pedigree_only_project: ImportProject,
    genotype_storage: GenotypeStorage,
) -> None:

    run_with_project(pedigree_only_project)

    gpf_instance = pedigree_only_project.get_gpf_instance()
    gpf_instance.reload()
    study = gpf_instance.get_genotype_data("pedigree_dataset")
    assert study is not None
