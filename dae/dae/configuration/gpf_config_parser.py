import os
import glob
import yaml
import json
import toml
from cerberus import Validator
from collections import namedtuple
from Typing import Dict, Any


class GPFConfigParser:

    filetype_parsers: Dict[str, Any] = {
        ".yaml": yaml.safe_load,
        ".json": json.loads,
        ".toml": toml.loads,
    }

    section_schemas: Dict[str, Dict[str, Any]] = {"studyconfig": None}

    @classmethod
    def _dict_to_namedtuple(cls, input_dict: Dict[str, Any], dict_name: str = "root"):
        tup_ctor = namedtuple(dict_name, input_dict.keys())

        for key, value in input_dict.items():
            if isinstance(value, dict):
                input_dict[key] = cls._dict_to_namedtuple(value, key)

        return tup_ctor(*input_dict.values())

    @classmethod
    def _read_config(cls, filename: str) -> Dict[str, Any]:
        ext = os.path.splitext(filename)[1]
        assert ext in cls.filetype_parsers, f"Unsupported filetype {filename}!"
        conf_dict = cls.filetype_parsers[ext](filename)
        return conf_dict

    @classmethod
    def _read_directory_configs(cls, dirname):
        config_files = list()
        for filetype in cls.filetype_parsers.keys():
            config_files += glob.glob(os.path.join(dirname, f"*{filetype}"))

        return list(map(cls.read_config, config_files))

    @classmethod
    def _validate_config(cls, config):
        first_section = config.keys()[0]
        schema = cls.section_schemas[first_section]
        v = Validator(schema)
        assert v.validate(config), v.errors

        return v.document

    @classmethod
    def load_config(cls, filename):
        config = cls._validate_config(cls._read_config(filename))
        return cls._dict_to_namedtuple(config)
