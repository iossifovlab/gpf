# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

from dae.import_tools.import_tools import ImportProject
from dae.inmemory_storage.inmemory_import_storage import InmemoryImportStorage


def test_simple_project_storage_type(simple_project: ImportProject) -> None:
    assert simple_project._storage_type() == "inmemory"


def test_simple_project_pedigree_params(simple_project: ImportProject) -> None:
    fname, params = simple_project.get_pedigree_params()

    assert fname.endswith("pedigree.ped")
    assert params["ped_family"] == "fId"
    assert params["ped_person"] == "pId"
    assert params["ped_mom"] == "mId"
    assert params["ped_dad"] == "dId"
    assert params["ped_tags"] is True


def test_simple_project_pedigree_size(simple_project: ImportProject) -> None:
    pedigree = simple_project.get_pedigree()
    assert len(pedigree) == 1
    assert len(pedigree.persons) == 5


def test_simple_project_destination_study_dir(
    simple_project: ImportProject,
) -> None:
    dest = InmemoryImportStorage._get_destination_study_dir(simple_project)
    assert dest.endswith("storage/test_import")
    assert os.path.exists(dest)


def test_simple_project_get_loader_types(
    simple_project: ImportProject,
) -> None:
    loader_types = simple_project.get_variant_loader_types()
    assert loader_types == {"denovo"}


def test_study_dir_pedigree(simple_project: ImportProject) -> None:
    dest = InmemoryImportStorage._do_copy_pedigree(simple_project)
    assert dest["path"].endswith("storage/test_import/pedigree.ped")
    assert os.path.exists(dest["path"])


def test_study_dir_denovo_variants(simple_project: ImportProject) -> None:
    dest = InmemoryImportStorage._do_copy_variants(simple_project, "denovo")
    assert len(dest) == 1

    assert dest[0]["path"].endswith(
        "storage/test_import/denovo.tsv")
    assert os.path.exists(dest[0]["path"][0])


def test_study_import(simple_project: ImportProject) -> None:
    InmemoryImportStorage._do_study_import(simple_project)
    gpf_instance = simple_project.get_gpf_instance()
    gpf_instance.reload()

    study = gpf_instance.get_genotype_data("test_import")
    fvs = list(study.query_variants())
    assert len(fvs) == 2
