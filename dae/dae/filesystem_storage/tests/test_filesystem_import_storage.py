# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from dae.filesystem_storage.filesystem_import_storage import \
    FilesystemImportStorage


def test_simple_project_storage_type(simple_project):
    assert simple_project._storage_type() == "filesystem"


def test_simple_project_pedigree_params(simple_project):
    fname, params = simple_project.get_pedigree_params()

    assert fname.endswith("pedigree.ped")
    assert params["ped_family"] == "fId"
    assert params["ped_person"] == "pId"
    assert params["ped_mom"] == "mId"
    assert params["ped_dad"] == "dId"


def test_simple_project_pedigree_size(simple_project):
    pedigree = simple_project.get_pedigree()
    assert len(pedigree) == 1
    assert len(pedigree.persons) == 5


def test_simple_project_destination_study_dir(simple_project):
    dest = FilesystemImportStorage._get_destination_study_dir(simple_project)
    assert dest.endswith("storage/test_import")
    assert os.path.exists(dest)


def test_simple_project_get_loader_types(simple_project):
    loader_types = simple_project.get_import_variants_types()
    assert loader_types == {"denovo"}


def test_study_dir_pedigree(simple_project):
    dest = FilesystemImportStorage._do_copy_pedigree(simple_project)
    assert dest["path"].endswith("storage/test_import/pedigree.ped")
    assert os.path.exists(dest["path"])


def test_study_dir_denovo_variants(simple_project):
    dest = FilesystemImportStorage._do_copy_variants(simple_project, "denovo")
    assert len(dest) == 1

    assert dest[0]["path"].endswith(
        "storage/test_import/denovo.tsv")
    assert os.path.exists(dest[0]["path"][0])


def test_study_import(simple_project):
    FilesystemImportStorage._do_study_import(simple_project)
    gpf_instance = simple_project.get_gpf_instance()
    gpf_instance.reload()

    study = gpf_instance.get_genotype_data("test_import")
    fvs = list(study.query_variants())
    assert len(fvs) == 2
