import os
import glob
import yaml
import json
import toml
from cerberus import Validator
from collections import namedtuple
from Typing import List, Tuple, Any


class GPFConfigParser:

    filetype_parsers: dict = {
        ".yaml": yaml.safe_load,
        ".json": json.loads,
        ".toml": toml.loads,
    }

    @classmethod
    def _dict_to_namedtuple(
        cls, input_dict: dict, dict_name: str = "root"
    ) -> Tuple[Any]:
        tup_ctor = namedtuple(dict_name, input_dict.keys())

        for key, value in input_dict.items():
            if isinstance(value, dict):
                input_dict[key] = cls._dict_to_namedtuple(value, key)

        return tup_ctor(*input_dict.values())

    @classmethod
    def _read_config(cls, filename: str) -> dict:
        ext = os.path.splitext(filename)[1]
        assert ext in cls.filetype_parsers, f"Unsupported filetype {filename}!"
        conf_dict = cls.filetype_parsers[ext](filename)
        return conf_dict

    @classmethod
    def _read_directory_configs(cls, dirname: str, schema: dict) -> List[dict]:
        config_files = list()
        for filetype in cls.filetype_parsers.keys():
            config_files += glob.glob(
                os.path.join(dirname, f"*{filetype}"), recursive=True
            )

        return list(map(cls.read_config, config_files))

    @classmethod
    def _validate_config(cls, config: dict, schema: dict) -> dict:
        v = Validator(schema)
        assert v.validate(config), v.errors

        return v.document

    @classmethod
    def _merge_config(cls, config: dict, default: dict) -> None:
        for key in default.keys():
            if key not in config.keys():
                config[key] = default[key]

    @classmethod
    def load_config(
        cls, filename: str, schema: dict, default_filename: str = None
    ) -> Tuple[Any]:
        config = cls._validate_config(cls._read_config(filename), schema)
        if default_filename:
            default_config = cls._validate_config(
                cls._read_config(default_filename), schema
            )
            cls._merge_config(config, default_config)
        return cls._dict_to_namedtuple(config)

    @classmethod
    def load_directory_configs(
        cls, dirname: str, schema: dict, default_filename: str
    ) -> List[Tuple[Any]]:
        configs = list(
            map(cls._validate_config, cls._read_directory_configs(dirname))
        )

        if default_filename:
            default_config = cls._validate_config(
                cls._read_config(default_filename), schema
            )
            for config in configs:
                cls._merge_config(config, default_config)

        return list(map(cls._load_config, configs))
