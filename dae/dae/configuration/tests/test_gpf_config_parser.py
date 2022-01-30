import pytest
import os

from box import BoxError
from dae.configuration.gpf_config_parser import GPFConfigParser, \
    DefaultBox, FrozenBox


def test_default_box():
    default_box = DefaultBox({"a": 123})
    assert default_box.a == 123
    assert default_box.non_existent_attr is None


def test_frozen_box():
    with pytest.raises(BoxError):
        frozen_box = FrozenBox({"a": 123})
        assert frozen_box.a == 123
        frozen_box.a = 456


def test_config_parser_load_single(conf_schema_basic, fixtures_dir):
    config = GPFConfigParser.load_config(
        os.path.join(fixtures_dir, "basic_conf.toml"), conf_schema_basic
    )
    print(config)
    assert config.id == "152135"
    assert config.name == "Basic test config"
    assert config.section1.someval1 == "beep"
    assert config.section1.someval2 == 1.23
    assert config.section1.someval3 == 52345


def test_config_parser_load_directory(conf_schema_basic, fixtures_dir):
    configs = GPFConfigParser.load_directory_configs(
        os.path.join(fixtures_dir, "sample_conf_directory"), conf_schema_basic
    )
    print(configs)

    assert len(configs) == 4
    configs = sorted(configs, key=lambda x: x.id)
    assert configs[0].id == "1"
    assert configs[0].name == "conf1"
    assert configs[1].id == "2"
    assert configs[1].name == "conf2"
    assert configs[2].id == "3"
    assert configs[2].name == "conf3"
    assert configs[3].id == "4"
    assert configs[3].name == "conf4"


def test_config_parser_string_interpolation(conf_schema_strings, fixtures_dir):
    config = GPFConfigParser.load_config(
        os.path.join(fixtures_dir, "vars_conf.toml"), conf_schema_strings
    )
    print(config)
    assert config.id == "152135"
    assert config.name == "Vars test config"
    assert config.vars is None
    assert config.section1.someval1 == "asdf"
    assert config.section1.someval2 == "ghjkl"
    assert config.section1.someval3 == "qwertyasdfghjk"


def test_config_parser_set_config(conf_schema_set, fixtures_dir):
    config = GPFConfigParser.load_config(
        os.path.join(fixtures_dir, "set_conf.toml"), conf_schema_set
    )
    print(config)
    assert config.id == "152135"
    assert config.name == "Set test config"
    assert config.section1.someval1 == "ala"
    assert isinstance(config.section1.someval2, set)
    assert (config.section1.someval2 ^ {"a", "b", "c", "d"}) == set()
    assert config.section1.someval3 == 123


def test_config_parser_load_paths(conf_schema_path, fixtures_dir, mocker):
    patch = mocker.patch("os.path.exists")
    patch.return_value = True
    config = GPFConfigParser.load_config(
        os.path.join(fixtures_dir, "path_conf.toml"), conf_schema_path
    )
    print(config)
    assert config.id == "152135"
    assert config.name == "Path test config"
    assert config.some_abs_path == "/tmp/maybesomeconf.toml"
    assert config.some_rel_path == os.path.join(
        fixtures_dir, "environ_conf.toml"
    )


def test_config_parser_load_incorrect_paths(conf_schema_path, fixtures_dir):
    with pytest.raises(ValueError):
        GPFConfigParser.load_config(
            os.path.join(fixtures_dir, "wrong_path_conf.toml"),
            conf_schema_path
        )


def test_config_parser_env_interpolation(
    conf_schema_basic, fixtures_dir, mocker
):
    mocker.patch.dict(os.environ, {"test_env_var": "bop"})
    config = GPFConfigParser.load_config(
        os.path.join(fixtures_dir, "env_interpolation_conf.toml"),
        conf_schema_basic,
    )

    print(config)
    assert config.id == "152135"
    assert config.name == "Environment interpolation test config"
    assert config.section1.someval1 == "bop"
    assert config.section1.someval2 == 1.23
    assert config.section1.someval3 == 52345


def test_config_parser_env_interpolation_missing(
    conf_schema_basic, fixtures_dir
):

    with pytest.raises(ValueError):
        GPFConfigParser.load_config(
            os.path.join(fixtures_dir, "env_interpolation_conf.toml"),
            conf_schema_basic,
        )
