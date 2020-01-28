import os
import glob

import yaml
import json
import toml

from collections import namedtuple, UserDict
from collections.abc import Collection, Mapping
from typing import List, Tuple, Any, Dict
from cerberus import Validator

from dae.utils.dict_utils import recursive_dict_update


def recursive_map(input_val, function):
    def apply_func(i):
        return recursive_map(i, function)

    if isinstance(input_val, Mapping):
        input_val = type(input_val)(
            {key: apply_func(val) for key, val in input_val.items()}
        )
    elif isinstance(input_val, Collection) and not isinstance(input_val, str):
        input_val = type(input_val)(apply_func(item) for item in input_val)
    return function(input_val)


def validate_path(field: str, value: str, error: str):
    if not os.path.isabs(value):
        error(field, "is not an absolute path!")
    if not os.path.exists(value):
        error(field, "does not exist!")


class LenientInterpolationDict(UserDict):
    """
    If a key is missing from the dictionary, returns
    it surrounded by curly braces. Allows interpolation
    of strings without providing all interpolation vars.
    """

    def __missing__(self, key):
        return "{%s}" % key


class GPFConfigValidator(Validator):
    def _normalize_coerce_abspath(self, value: str) -> str:
        directory = self._config["conf_dir"]
        if not os.path.isabs(value):
            value = os.path.join(directory, value)
        return os.path.normpath(value)


class GPFConfigParser:

    filetype_parsers: dict = {
        ".yaml": yaml.safe_load,
        ".json": json.loads,
        ".toml": toml.loads,
        ".conf": toml.loads,  # TODO FIXME Rename all .conf to .toml
    }

    @classmethod
    def _dict_to_namedtuple(
        cls, input_dict: dict, dict_name: str = "root"
    ) -> Tuple[Any]:
        if not isinstance(input_dict, dict):
            return input_dict
        tup_ctor = namedtuple(dict_name, input_dict.keys())

        class DefaultValueTuple(tup_ctor):
            def __getattr__(self, name):
                print(f'WARNING: Attempting to get non-existent attribute {name} on tuple!')
                return None

        return DefaultValueTuple(*input_dict.values())

    @classmethod
    def _namedtuple_to_dict(cls, tup: Tuple[Any]) -> Dict[str, Any]:
        output = tup._asdict()
        for k, v in output.items():
            if isinstance(v, tuple):
                output[k] = cls._namedtuple_to_dict(v)
        return output

    @classmethod
    def _interpolate_vars(
        cls, input_string: str, interpolation_vars: dict
    ) -> str:
        if not isinstance(input_string, str):
            return input_string
        return input_string.format_map(interpolation_vars)

    @classmethod
    def _interpolate_env(cls, input_string: str) -> str:
        env_vars = LenientInterpolationDict(
            {f"${key}": val for key, val in os.environ.items()}
        )
        return cls._interpolate_vars(input_string, env_vars)

    @classmethod
    def _read_config(cls, filename: str) -> dict:
        ext = os.path.splitext(filename)[1]
        assert ext in cls.filetype_parsers, f"Unsupported filetype {filename}!"
        with open(filename, "r") as infile:
            conf_dict = cls.filetype_parsers[ext](infile.read())
        return conf_dict

    @classmethod
    def _collect_directory_configs(cls, dirname: str) -> List[str]:
        config_files = list()
        for filetype in cls.filetype_parsers.keys():
            config_files += glob.glob(
                os.path.join(dirname, f"**/*{filetype}"), recursive=True
            )
        return config_files

    @classmethod
    def load_config(
        cls, filename: str, schema: dict, default_filename: str = None
    ) -> Tuple[Any]:
        validator = GPFConfigValidator(
            schema, conf_dir=os.path.dirname(filename)
        )

        config = cls._read_config(filename)
        default_config = (
            cls._read_config(default_filename) if default_filename else dict()
        )

        config = recursive_dict_update(config, default_config)

        config = recursive_map(config, cls._interpolate_env)
        if "vars" in config:
            config = recursive_map(
                config, lambda c: cls._interpolate_vars(c, config["vars"])
            )
            del config["vars"]

        assert validator.validate(config), validator.errors
        return recursive_map(validator.document, cls._dict_to_namedtuple)

    @classmethod
    def load_directory_configs(
        cls, dirname: str, schema: dict, default_filename: str = None
    ) -> List[Tuple[Any]]:
        return [
            cls.load_config(config_path, schema, default_filename)
            for config_path in cls._collect_directory_configs(dirname)
        ]

    @classmethod
    def modify_tuple(
        cls, t: Tuple[Any], new_values: Dict[str, Any]
    ) -> Tuple[Any]:
        t_dict = cls._namedtuple_to_dict(t)
        updated_dict = recursive_dict_update(t_dict, new_values)
        return recursive_map(updated_dict, cls._dict_to_namedtuple)
