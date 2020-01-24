import os
import glob
import re

import yaml
import json
import toml

from copy import deepcopy
from collections import namedtuple
from typing import List, Tuple, Any, Dict
from cerberus import Validator

from dae.utils.dict_utils import recursive_dict_update


def validate_path(field: str, value: str, error: str):
    if not os.path.isabs(value):
        error(field, "is not an absolute path!")
    if not os.path.exists(value):
        error(field, "does not exist!")


class GPFConfigValidator(Validator):
    def _normalize_coerce_abspath(self, value: str) -> str:
        directory = self._config["conf_dir"]
        if not os.path.isabs(value):
            value = os.path.join(directory, value)
        return os.path.normpath(value)


class GPFConfigParser:

    interpolation_var_regex: str = r"%\(([A-Za-z0-9_]+)\)s"
    interpolation_env_regex: str = r"%\(([A-Za-z0-9_]+)\)e"

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
    def _interpolate_vars(
        cls, input_dict: dict, **interpolation_vars: str
    ) -> dict:
        result_dict = deepcopy(input_dict)

        for key, val in result_dict.items():
            if isinstance(val, str):
                matched_var_interpolations = re.findall(
                    cls.interpolation_var_regex, val
                )
                for interpolation in matched_var_interpolations:
                    assert interpolation in interpolation_vars, (
                        f"Undefined var '{interpolation}'!"
                        " Defined vars: {interpolation_vars.keys()}"
                    )
                    result_dict[key] = result_dict[key].replace(
                        f"%({interpolation})s",
                        interpolation_vars[interpolation],
                    )

                matched_env_interpolations = re.findall(
                    cls.interpolation_env_regex, val
                )
                for interpolation in matched_env_interpolations:
                    assert (
                        interpolation in os.environ.keys()
                    ), f"Environment variable '{interpolation}' not found!"
                    env_value = os.environ.get(interpolation)
                    result_dict[key] = result_dict[key].replace(
                        f"%({interpolation})e", env_value
                    )

            elif isinstance(val, dict):
                result_dict[key] = cls._interpolate_vars(
                    val, **interpolation_vars
                )

        return result_dict

    @classmethod
    def _interpolate_env(cls, input_dict: dict) -> dict:
        result_dict = deepcopy(input_dict)

        for key, val in result_dict.items():
            if isinstance(val, str):
                matched_env_interpolations = re.findall(
                    cls.interpolation_env_regex, val
                )
                for interpolation in matched_env_interpolations:
                    assert (
                        interpolation in os.environ.keys()
                    ), f"Environment variable '{interpolation}' not found!"
                    env_value = os.environ.get(interpolation)
                    result_dict[key] = result_dict[key].replace(
                        f"%({interpolation})e", env_value
                    )

            elif isinstance(val, dict):
                result_dict[key] = cls._interpolate_env(val)

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

        config = cls._interpolate_env(config)
        if "vars" in config:
            config = cls._interpolate_vars(config, **config["vars"])
            del config["vars"]

        assert validator.validate(config), validator.errors
        return cls._dict_to_namedtuple(validator.document)

    @classmethod
    def load_directory_configs(
        cls, dirname: str, schema: dict, default_filename: str = None
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
