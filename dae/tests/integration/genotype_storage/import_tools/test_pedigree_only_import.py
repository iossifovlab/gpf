# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.cli import run_with_project
from dae.import_tools.import_tools import ImportProject
from dae.testing import alla_gpf, setup_pedigree
from dae.testing.import_helpers import StudyInputLayout, pedigree_import


@pytest.fixture(scope="module")
def pedigree_only_import_data(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> tuple[pathlib.Path, GPFInstance, StudyInputLayout]:
    root_path = tmp_path_factory.mktemp("test_pedigree_only_import")

    gpf_instance = alla_gpf(root_path, genotype_storage_factory(root_path))

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
    pedigree_only_import_data: tuple[
        pathlib.Path, GPFInstance, StudyInputLayout],
) -> ImportProject:
    root_path, gpf_instance, layout = pedigree_only_import_data

    return pedigree_import(
        root_path,
        "pedigree_dataset", layout.pedigree,
        gpf_instance,
    )


def test_pedigree_only_import(
    pedigree_only_project: ImportProject,
) -> None:

    run_with_project(pedigree_only_project)

    gpf_instance = pedigree_only_project.get_gpf_instance()
    gpf_instance.reload()
    study = gpf_instance.get_genotype_data("pedigree_dataset")
    assert study is not None
