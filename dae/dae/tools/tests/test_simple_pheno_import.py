import pytest

from dae.tools.simple_pheno_import import verify_phenotype_data_name


def test_verify_valid_pheno_db_name():
    assert verify_phenotype_data_name("a") == "a"
    assert verify_phenotype_data_name("a/") == "a"
    assert verify_phenotype_data_name("a//") == "a"


def test_verify_invalid_pheno_db_name():
    with pytest.raises(AssertionError) as excinfo:
        verify_phenotype_data_name("a/b")
    assert str(excinfo.value) == '"a/b" is a directory path!'

    with pytest.raises(AssertionError) as excinfo:
        verify_phenotype_data_name("a/b/")
    assert str(excinfo.value) == '"a/b" is a directory path!'

    with pytest.raises(AssertionError) as excinfo:
        verify_phenotype_data_name("a/b//")
    assert str(excinfo.value) == '"a/b" is a directory path!'

    with pytest.raises(AssertionError) as excinfo:
        verify_phenotype_data_name("/a")
    assert str(excinfo.value) == '"/a" is a directory path!'

    with pytest.raises(AssertionError) as excinfo:
        verify_phenotype_data_name("/a/")
    assert str(excinfo.value) == '"/a" is a directory path!'
