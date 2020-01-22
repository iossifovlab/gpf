import os
from dae.dae.configuration.gpf_config_parser import GPFConfigParser


def test_config_parser_load_single(conf_validator_basic, fixtures_dir):
    config = GPFConfigParser.load_config(
        os.path.join(fixtures_dir, "basic_conf.toml")
    )
    print(config)
