import os
import glob
import re

import yaml
import json
import toml

from copy import deepcopy
from collections import namedtuple
from typing import Union, List, Tuple, Any, Callable, Dict
from cerberus import Validator

from dae.utils.dict_utils import recursive_dict_update


def environ_override(field: str) -> Callable:
    return lambda value: os.environ.get(field, None) or value


class GPFConfigValidator(Validator):
    def _validate_path(
        self, path: Union[List[str], Tuple[str]], field: str, value: str
    ):
        assert path in ("relative", "absolute")
        if path == "absolute":
            assert os.path.isabs(value)
            assert os.path.exists(value)
        else:
            assert not os.path.isabs(value)


class GPFConfigNormalizer:
    """
    Custom normalizer which utilizes the schema provided to
    Cerberus' validator.
    """

    def __init__(self, config_file_directory: str):
        self.config_file_directory = config_file_directory

    def resolve_relative_path(self, relative_path: str):
        abspath = os.path.join(self.config_file_path, relative_path)
        assert os.path.isabs(abspath), abspath
        assert os.path.exists(abspath), abspath
        return abspath

    def normalize_value(self, field: str, value: Any, rules: dict) -> Any:
        if rules.get("path") == "relative":
            return self.resolve_relative_path(value)
        return value

    def normalize(
        self, config: dict, schema: dict, default_rules: dict = None
    ) -> dict:
        normalized_config = dict()
        for key, value in config.items():
            rules = schema[key] if key in schema else default_rules
            if isinstance(value, dict):
                normalized_config[key] = self.normalize(
                    config[key],
                    rules.get("schema", dict()),
                    rules.get("valuesrules", None),
                )
            else:
                normalized_config[key] = self.normalize_value(
                    key, value, rules
                )
        return normalized_config


class GPFConfigParser:

    interpolation_var_regex: str = r"%\(([A-Za-z0-9_]+)\)s"

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
        tup_ctor = namedtuple(dict_name, input_dict.keys())

        for key, value in input_dict.items():
            if isinstance(value, dict):
                input_dict[key] = cls._dict_to_namedtuple(value, key)

        return tup_ctor(*input_dict.values())

    @classmethod
    def _namedtuple_to_dict(cls, tup: Tuple[Any]) -> Dict[str, Any]:
        output = tup._asdict()
        for k, v in output.items():
            if isinstance(v, tuple):
                output[k] = cls._namedtuple_to_dict(v)
        return output

    @classmethod
    def _interpolate(cls, input_dict: dict, **interpolation_vars: str) -> dict:
        result_dict = deepcopy(input_dict)

        for key, val in result_dict.items():
            if isinstance(val, str):
                matched_interpolations = re.findall(
                    cls.interpolation_var_regex, val
                )
                for interpolation in matched_interpolations:
                    assert interpolation in interpolation_vars, (
                        f"Undefined var '{interpolation}'!"
                        " Defined vars: {interpolation_vars.keys()}"
                    )
                    result_dict[key] = result_dict[key].replace(
                        f"%({interpolation})s",
                        interpolation_vars[interpolation],
                    )
            elif isinstance(val, dict):
                result_dict[key] = cls._interpolate(val, **interpolation_vars)

        return result_dict

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
        cls, filename: str, schema: dict = None, default_filename: str = None
    ) -> Tuple[Any]:

        validator = GPFConfigValidator(schema)
        normalizer = GPFConfigNormalizer(os.path.dirname(filename))

        config = cls._read_config(filename)
        default_config = (
            cls._read_config(default_filename) if default_filename else dict()
        )

        config = recursive_dict_update(config, default_config)
        if "vars" in config:
            config = cls._interpolate(config, **config["vars"])
            del config["vars"]

        if schema:
            # TODO Remove this behaviour! (and schema default value None)
            # This is a temporary crutch to fix the unit tests
            # without creating all schemas beforehand.
            # We do NOT want to allow lack of validation.
            assert validator.validate(config), validator.errors
            config = normalizer.normalize(validator.document, schema)

        return cls._dict_to_namedtuple(config)

    @classmethod
    def load_directory_configs(
        cls, dirname: str, schema: dict = None, default_filename: str = None
    ) -> List[Tuple[Any]]:
        return [
            cls.load_config(config_path, schema, default_filename)
            for config_path in cls._collect_directory_configs(dirname)
        ]

    @classmethod
    def _update_dict(cls, d: Dict[str, Any], updated_vals: Dict[str, Any]):
        for k, v in updated_vals.items():
            if isinstance(v, dict):
                d[k] = cls._update_dict(d.get(k), v)
            else:
                d[k] = v
        return d

    @classmethod
    def modify_tuple(
        cls, t: Tuple[Any], new_values: Dict[str, Any]
    ) -> Tuple[Any]:
        t_dict = cls._namedtuple_to_dict(t)
        updated_dict = cls._update_dict(t_dict, new_values)
        return cls._dict_to_namedtuple(updated_dict)
