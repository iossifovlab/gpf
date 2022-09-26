# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from dae.impala_storage.import_commons import DatasetHelpers


def test_find_genotype_data_config_file(fixtures_gpf_instance):
    helpers = DatasetHelpers(fixtures_gpf_instance)
    fname = helpers.find_genotype_data_config_file("Study1")
    assert fname is not None


def test_find_genotype_data_config(fixtures_gpf_instance):
    print(fixtures_gpf_instance.get_genotype_data_ids())
    helpers = DatasetHelpers(fixtures_gpf_instance)
    res = helpers.find_genotype_data_config("Study1")

    assert res is not None
    assert res.id == "Study1"


def test_is_impala_genotype_data_config(fixtures_gpf_instance):
    print(fixtures_gpf_instance.get_genotype_data_ids())
    helpers = DatasetHelpers(fixtures_gpf_instance)
    assert not helpers.is_impala_genotype_storage("Study1")


def test_check_dataset_rename_hdfs_directory(
        fixtures_gpf_instance, data_import):
    helpers = DatasetHelpers(fixtures_gpf_instance)

    sdir, ddir = helpers.check_dataset_rename_hdfs_directory("Study1", "new")
    assert sdir is None and ddir is None

    sdir, ddir = helpers.check_dataset_rename_hdfs_directory(
        "SVMergingStudy1", "new")
    assert sdir is not None and ddir is not None


def test_check_dataset_hdfs_directory(
        fixtures_gpf_instance, data_import):
    helpers = DatasetHelpers(fixtures_gpf_instance)

    assert not helpers.check_dataset_hdfs_directories(
        helpers.get_genotype_storage("Study1"), "Study1")
    assert helpers.check_dataset_hdfs_directories(
        helpers.get_genotype_storage("SVMergingStudy1"), "SVMergingStudy1")


def test_dataset_rename_hdfs_directory(
        fixtures_gpf_instance, mocker, data_import):
    def mock_rename(self, name1, name2):
        assert name1.endswith("SVMergingStudy1")
        assert name2.endswith("new")

    mocker.patch(
        "dae.impala_storage.hdfs_helpers.HdfsHelpers.rename",
        mock_rename)

    helpers = DatasetHelpers(fixtures_gpf_instance)
    helpers.dataset_rename_hdfs_directory("SVMergingStudy1", "new")


def test_dataset_delete_hdfs_directory(
        fixtures_gpf_instance, mocker, data_import):
    def mock_delete(self, name, recursive):
        assert name.endswith("SVMergingStudy1")
        assert recursive

    mocker.patch(
        "dae.impala_storage.hdfs_helpers.HdfsHelpers.delete",
        mock_delete)

    helpers = DatasetHelpers(fixtures_gpf_instance)
    helpers.dataset_remove_hdfs_directory("SVMergingStudy1")


def test_dataset_recreate_impala_tables(
        fixtures_gpf_instance, mocker, data_import):
    def mock_recreate(self, db, old_table, new_table, hdfs_dir):
        print(old_table)
        print(new_table)
        print(hdfs_dir)
        assert old_table.startswith("svmergingstudy1")
        assert new_table.startswith("new")
        assert "/new/" in hdfs_dir

    mocker.patch(
        "dae.impala_storage.impala_helpers.ImpalaHelpers.recreate_table",
        mock_recreate)

    helpers = DatasetHelpers(fixtures_gpf_instance)
    mocker.patch.object(
        helpers, "check_dataset_hdfs_directories", return_value=True)

    helpers.dataset_recreate_impala_tables("SVMergingStudy1", "new")


def test_dataset_drop_impala_tables(
        fixtures_gpf_instance, mocker, data_import):
    def mock_drop(self, db, table,):
        print(table)
        assert table.startswith("svmergingstudy1")

    mocker.patch(
        "dae.impala_storage.impala_helpers.ImpalaHelpers.drop_table",
        mock_drop)

    helpers = DatasetHelpers(fixtures_gpf_instance)
    # mocker.patch.object(
    #     helpers, "check_dataset_hdfs_directories", return_value=True)

    helpers.dataset_drop_impala_tables("SVMergingStudy1")


def test_check_dataset_impala_tables(
        fixtures_gpf_instance, mocker, data_import):

    helpers = DatasetHelpers(fixtures_gpf_instance)

    helpers.check_dataset_impala_tables("SVMergingStudy1")


def test_rename_study_config(fixtures_gpf_instance, mocker):
    def mock_rename(name1, name2):
        print(name1)
        print(name2)

    mocker.patch("os.rename", mock_rename)

    mock_open = mocker.mock_open()
    mocker.patch("dae.impala_storage.import_commons.open", mock_open)

    spy = mocker.spy(os, "rename")

    helpers = DatasetHelpers(fixtures_gpf_instance)

    helpers.rename_study_config("SVMergingStudy1", "new", {})

    print(spy.mock_calls)
    print(mock_open.mock_calls)

    assert len(spy.mock_calls) == 2
    assert len(mock_open.mock_calls) == 4


def test_remove_study_config(fixtures_gpf_instance, mocker):
    def mock_remove(fname):
        assert fname.endswith("SVMergingStudy1")

    mocker.patch("shutil.rmtree", mock_remove)

    helpers = DatasetHelpers(fixtures_gpf_instance)
    helpers.remove_study_config("SVMergingStudy1")
