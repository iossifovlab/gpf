# pylint: disable=W0621,C0114,C0116,W0212,W0613
import re
import pytest

from dae.inmemory_storage.inmemory_genotype_storage import \
    InmemoryGenotypeStorage


def test_validate_config():
    config = {
        "storage_type": "inmemory",
        "id": "aaaa",
        "dir": "/tmp/aaaa_filesystem"
    }
    res = InmemoryGenotypeStorage.validate_and_normalize_config(config)
    assert res is not None


def test_validate_config_missing_id():
    config = {
        "storage_type": "inmemory",
        "dir": "/tmp/aaaa_filesystem"
    }
    with pytest.raises(
            ValueError,
            match="genotype storage without ID; 'id' is required"):
        InmemoryGenotypeStorage.validate_and_normalize_config(config)


def test_validate_config_missing_storage_type():
    config = {
        "id": "aaaa",
        "dir": "/tmp/aaaa_filesystem"
    }
    with pytest.raises(
            ValueError,
            match="genotype storage without type; 'storage_type' is required"):
        InmemoryGenotypeStorage.validate_and_normalize_config(config)


def test_validate_config_wrong_storage_type():
    config = {
        "id": "aaaa",
        "storage_type": "filesystem2",
        "dir": "/tmp/aaaa_filesystem"
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "storage configuration for <filesystem2> passed to "
                "genotype storage class type <inmemory>")):
        InmemoryGenotypeStorage.validate_and_normalize_config(config)


def test_validate_config_missing_dir():
    config = {
        "id": "aaaa",
        "storage_type": "inmemory",
        # "dir": "/tmp/aaaa_filesystem"
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for inmemory storage: "
                "{'dir': ['required field']}")):
        InmemoryGenotypeStorage.validate_and_normalize_config(config)


def test_validate_config_bad_dir():
    config = {
        "id": "aaaa",
        "storage_type": "inmemory",
        "dir": "tmp/aaaa_filesystem"
    }
    with pytest.raises(
            ValueError,
            match=re.escape(
                "wrong config format for inmemory storage: "
                "{'dir': ['path <tmp/aaaa_filesystem> "
                "is not an absolute path']}")):
        InmemoryGenotypeStorage.validate_and_normalize_config(config)
