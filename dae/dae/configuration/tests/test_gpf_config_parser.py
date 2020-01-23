import pytest
import os
from dae.configuration.gpf_config_parser import GPFConfigParser


def test_config_parser_load_single(conf_schema_basic, fixtures_dir):
    config = GPFConfigParser.load_config(
        os.path.join(fixtures_dir, "basic_conf.toml"), conf_schema_basic
    )
    assert config.id == "152135"
    assert config.name == "Basic test config"
    assert config.section1.someval1 == "beep"
    assert config.section1.someval2 == 1.23
    assert config.section1.someval3 == 52345
    print(config)


def test_config_parser_load_directory(conf_schema_basic, fixtures_dir):
    pass


def test_config_parser_load_environment_variable(conf_schema_environ, fixtures_dir):
    pass


def test_config_parser_load_absolute_path(conf_schema_path, fixtures_dir):
    pass


@pytest.mark.xfail("Relative paths are not supported")
def test_config_parser_load_relative_path(conf_schema_path, fixtures_dir):
    pass
