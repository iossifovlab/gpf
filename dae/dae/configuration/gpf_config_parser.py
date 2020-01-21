import os
import glob
import re

import yaml
import json
import toml

from copy import deepcopy
from collections import namedtuple
from Typing import List, Tuple, Any, Callable
from cerberus import Validator

from dae.utils.dict_utils import recursive_dict_update


def environ_override(field: str) -> Callable:
    return lambda value: os.environ.get(field, None) or value


class GPFConfigParser:

    interpolation_var_regex = r"%\(([A-Za-z0-9_]+)\)s"

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
    def _interpolate(cls, input_dict, **interpolation_vars):
        result_dict = deepcopy(input_dict)

        for key, val in result_dict.items():
            if isinstance(val, str):
                matched_interpolations = re.findall(
                    cls.interpolation_vars, val
                )
                for interpolation in matched_interpolations:
                    assert (
                        interpolation in interpolation_vars
                    ), (f"Undefined var '{interpolation}'!"
                        " Defined vars: {interpolation_vars.keys()}")
                    result_dict[key] = val.replace(
                        f"%({interpolation})s",
                        interpolation_vars[interpolation],
                    )
            elif isinstance(val, dict):
                result_dict[key] = cls._interpolate(val, interpolation_vars)

        return result_dict

    @classmethod
    def _read_config(cls, filename: str) -> dict:
        ext = os.path.splitext(filename)[1]
        assert ext in cls.filetype_parsers, f"Unsupported filetype {filename}!"
        conf_dict = cls.filetype_parsers[ext](filename)
        if "vars" in conf_dict:
            conf_dict = cls._interpolate(conf_dict, **conf_dict["vars"])
            del(conf_dict["vars"])
        return conf_dict

    @classmethod
    def _collect_directory_configs(cls, dirname: str) -> List[str]:
        config_files = list()
        for filetype in cls.filetype_parsers.keys():
            config_files += glob.glob(
                os.path.join(dirname, f"*{filetype}"), recursive=True
            )
        return config_files

    @classmethod
    def _validate_config(cls, config: dict, schema: dict) -> dict:
        v = Validator(schema)
        assert v.validate(config), v.errors

        return v.document

    @classmethod
    def load_config(
        cls, filename: str, schema: dict, default_filename: str = None
    ) -> Tuple[Any]:
        config = cls._validate_config(cls._read_config(filename), schema)
        if default_filename:
            default_config = cls._validate_config(
                cls._read_config(default_filename), schema
            )
            config = recursive_dict_update(config, default_config)
        return cls._dict_to_namedtuple(config)

    @classmethod
    def load_directory_configs(
        cls, dirname: str, schema: dict, default_filename: str = None
    ) -> List[Tuple[Any]]:
        return [
            cls.load_config(config_path, schema, default_filename)
            for config_path in cls._collect_directory_configs(dirname)
        ]
