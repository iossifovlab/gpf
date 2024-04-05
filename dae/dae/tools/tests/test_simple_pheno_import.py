# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.tools.pheno_import import verify_phenotype_data_name


def test_verify_valid_pheno_db_name() -> None:
    assert verify_phenotype_data_name("a") == "a"
    assert verify_phenotype_data_name("a/") == "a"
    assert verify_phenotype_data_name("a//") == "a"


def test_verify_invalid_pheno_db_name() -> None:
    with pytest.raises(AssertionError) as excinfo:
        verify_phenotype_data_name("a/b")
    assert str(excinfo.value) == "'a/b' is a directory path!"

    with pytest.raises(AssertionError) as excinfo:
        verify_phenotype_data_name("a/b/")
    assert str(excinfo.value) == "'a/b' is a directory path!"

    with pytest.raises(AssertionError) as excinfo:
        verify_phenotype_data_name("a/b//")
    assert str(excinfo.value) == "'a/b' is a directory path!"

    with pytest.raises(AssertionError) as excinfo:
        verify_phenotype_data_name("/a")
    assert str(excinfo.value) == "'/a' is a directory path!"

    with pytest.raises(AssertionError) as excinfo:
        verify_phenotype_data_name("/a/")
    assert str(excinfo.value) == "'/a' is a directory path!"
