import pytest
import os
from dae.configuration.gpf_config_parser import environ_override

sample_conf_schema_1 = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "section1": {
        "type": "dict",
        "schema": {
            "someval1": {"type": "string"},
            "someval2": {"type": "float"},
            "someval3": {"type": "integer"},
        },
    },
}

sample_conf_schema_2 = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "section1": {
        "type": "dict",
        "schema": {
            "someval1": {"type": "string"},
            "someval2": {"type": "string"},
            "someval3": {"type": "string"},
        },
    },
}

sample_conf_schema_3 = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "section1": {
        "type": "dict",
        "schema": {
            "someval1": {"type": "string"},
            "someval2": {
                "type": "set",
                "coerce": set,
                "schema": {"type": "string"},
            },
            "someval3": {"type": "integer"},
        },
    },
}

sample_conf_schema_4 = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "some_environ_var": {
        "type": "string",
        "coerce": environ_override("environ_test"),
    },
}

sample_conf_schema_5 = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "some_abs_path": {"type": "string", "path": "absolute"},
    "some_rel_path": {"type": "string", "path": "relative"},
}


def relative_to_this_test_folder(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.fixture(scope="session")
def fixtures_dir():
    return relative_to_this_test_folder("fixtures")


@pytest.fixture(scope="session")
def conf_schema_basic():
    return sample_conf_schema_1


@pytest.fixture(scope="session")
def conf_schema_strings():
    return sample_conf_schema_2


@pytest.fixture(scope="session")
def conf_schema_set():
    return sample_conf_schema_3


@pytest.fixture(scope="session")
def conf_schema_environ():
    return sample_conf_schema_4


@pytest.fixture(scope="session")
def conf_schema_path():
    return sample_conf_schema_5
