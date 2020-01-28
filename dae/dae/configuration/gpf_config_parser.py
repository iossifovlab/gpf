import os
import glob

import yaml
import json
import toml

from collections import namedtuple
from typing import List, Tuple, Any, Dict
from cerberus import Validator

from dae.utils.dict_utils import recursive_dict_update


def validate_path(field: str, value: str, error: str):
    print(field, value)
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

        class DefaultValueTuple(tup_ctor):
            def __getattr__(self, name):
                print(f'WARNING: Attempting to get non-existent attribute {name} on tuple!')
                return None

            def __repr__(self):
                retval = super(DefaultValueTuple, self).__repr__()
                return retval.replace('DefaultValueTuple', self.section_id())

            def section_id(self):
                return dict_name

        for key, value in input_dict.items():
            if isinstance(value, dict):
                input_dict[key] = cls._dict_to_namedtuple(value, key)
            elif isinstance(value, list):
                input_dict[key] = [
                    (cls._dict_to_namedtuple(item)
                     if isinstance(item, dict) else item)
                    for item in value
                ]

        return DefaultValueTuple(*input_dict.values())

    @classmethod
    def _namedtuple_to_dict(cls, tup: Tuple[Any]) -> Dict[str, Any]:
        output = tup._asdict()
        for k, v in output.items():
            if isinstance(v, tuple):
                output[k] = cls._namedtuple_to_dict(v)
        return output

    @classmethod
    def _collect_directory_configs(cls, dirname: str) -> List[str]:
        config_files = list()
        for filetype in cls.filetype_parsers.keys():
            config_files += glob.glob(
                os.path.join(dirname, f"**/*{filetype}"), recursive=True
            )
        return config_files

    @classmethod
    def parse_config(cls, filename: str) -> dict:
        ext = os.path.splitext(filename)[1]
        assert ext in cls.filetype_parsers, f"Unsupported filetype {filename}!"
        with open(filename, "r") as infile:
            file_contents = infile.read()

        interpol_vars = cls.filetype_parsers[ext](file_contents).get("vars", {})
        env_vars = {f"${key}": val for key, val in os.environ.items()}
        interpol_vars.update(env_vars)

        interpolated_text = file_contents % interpol_vars
        config = cls.filetype_parsers[ext](interpolated_text)
        config.pop("vars", None)
        return config

    @classmethod
    def load_config(
        cls, filename: str, schema: dict, default_filename: str = None
    ) -> Tuple[Any]:
        validator = GPFConfigValidator(
            schema, conf_dir=os.path.dirname(filename)
        )

        config = cls.parse_config(filename)
        if default_filename:
            default_config = cls.parse_config(default_filename)
            config = recursive_dict_update(config, default_config)

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
    def modify_tuple(
        cls, t: Tuple[Any], new_values: Dict[str, Any]
    ) -> Tuple[Any]:
        t_dict = cls._namedtuple_to_dict(t)
        updated_dict = recursive_dict_update(t_dict, new_values)
        return cls._dict_to_namedtuple(updated_dict)
