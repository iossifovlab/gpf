import os
import sys
import glob

import yaml
import toml

from collections import namedtuple
from copy import deepcopy
from typing import List, Any, Dict, NamedTuple
from cerberus import Validator

from dae.utils.dict_utils import recursive_dict_update


def validate_existing_path(field: str, value: str, error):
    if not os.path.isabs(value):
        error(field, f"path <{value}> is not an absolute path!")
    if not os.path.exists(value):
        error(field, f"path <{value}> does not exist!")


def validate_path(field: str, value: str, error):
    if not os.path.isabs(value):
        error(field, f"path <{value}> is not an absolute path!")


class GPFConfigValidator(Validator):
    def _normalize_coerce_abspath(self, value: str) -> str:
        directory = self._config["conf_dir"]
        if not os.path.isabs(value):
            value = os.path.join(directory, value)
        return os.path.normpath(value)


class GPFConfigParser:

    filetype_parsers: dict = {
        ".yaml": yaml.safe_load,
        # ".json": json.loads,
        ".toml": toml.loads,
        ".conf": toml.loads,  # TODO FIXME Rename all .conf to .toml
    }

    @classmethod
    def _dict_to_namedtuple(
        cls, input_dict: dict, dict_name: str = "root"
    ) -> NamedTuple:
        CONFIG_TUPLE = namedtuple(dict_name, input_dict.keys())  # type: ignore

        class ConfigTuple(CONFIG_TUPLE):  # noqa
            def __getattr__(self, name):
                # print(
                #     f"WARNING: Attempting to get non-existent attribute "
                #     f"{name} on tuple!",
                #     file=sys.stderr,
                # )

                # FIXME Temporary hack to enable default values
                # only for public attributes
                if name[0:2] == "__":
                    raise AttributeError()
                return None

            def __repr__(self):
                retval = super(ConfigTuple, self).__repr__()
                return retval.replace("ConfigTuple", self.section_id())

            def section_id(self):
                return dict_name

            def field_values_iterator(self):
                return zip(self._fields, self)

        for key, value in input_dict.items():
            if isinstance(value, dict):
                input_dict[key] = cls._dict_to_namedtuple(value, key)
            elif isinstance(value, list):
                input_dict[key] = [
                    (
                        cls._dict_to_namedtuple(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]

        return ConfigTuple(*input_dict.values())  # type: ignore

    @classmethod
    def _namedtuple_to_dict(cls, tup: NamedTuple) -> Dict[str, Any]:
        output = deepcopy(tup)._asdict()
        for k, v in output.items():
            if isinstance(v, tuple):
                output[k] = cls._namedtuple_to_dict(v)  # type: ignore
            if isinstance(v, list):
                for idx, li in enumerate(output[k]):
                    if isinstance(li, tuple):
                        output[k][idx] = cls._namedtuple_to_dict(li)  # type: ignore
        return output

    @classmethod
    def _collect_directory_configs(cls, dirname: str) -> List[str]:
        config_files: List[str] = list()
        for filetype in cls.filetype_parsers.keys():
            config_files += glob.glob(
                os.path.join(dirname, f"**/*{filetype}"), recursive=True
            )
        return config_files

    @classmethod
    def _get_file_contents(cls, filename: str) -> str:
        with open(filename, "r") as infile:
            return infile.read()

    @classmethod
    def parse_config(cls, filename: str) -> dict:
        ext = os.path.splitext(filename)[1]
        assert ext in cls.filetype_parsers, f"Unsupported filetype {filename}!"
        file_contents = cls._get_file_contents(filename)

        env_vars = {f"${key}": val for key, val in os.environ.items()}

        interpol_vars = cls.filetype_parsers[ext](file_contents).get(
            "vars", {}
        )
        interpol_vars = {
            key: value % env_vars for key, value in interpol_vars.items()
        }
        interpol_vars.update(env_vars)

        interpolated_text = file_contents % interpol_vars
        config = cls.filetype_parsers[ext](interpolated_text)
        config.pop("vars", None)
        return config  # type: ignore

    @classmethod
    def load_config(
        cls, filename: str, schema: dict, default_config_filename: str = None
    ) -> NamedTuple:
        assert os.path.exists(filename), f"{filename} does not exist!"

        validator = GPFConfigValidator(
            schema, conf_dir=os.path.dirname(filename)
        )

        config = cls.parse_config(filename)
        if default_config_filename:
            default_config = cls.parse_config(default_config_filename)
            config = recursive_dict_update(default_config, config)

        assert validator.validate(config), validator.errors
        return cls._dict_to_namedtuple(validator.document)

    @classmethod
    def load_config_raw(cls, filename: str) -> Dict[str, Any]:
        ext = os.path.splitext(filename)[1]
        assert ext in cls.filetype_parsers, f"Unsupported filetype {filename}!"
        file_contents = cls._get_file_contents(filename)
        return cls.filetype_parsers[ext](file_contents)  # type: ignore

    @classmethod
    def load_directory_configs(
        cls, dirname: str, schema: dict, default_config_filename: str = None
    ) -> List[NamedTuple]:
        return [
            cls.load_config(config_path, schema, default_config_filename)
            for config_path in cls._collect_directory_configs(dirname)
        ]

    @classmethod
    def modify_tuple(
        cls, t: NamedTuple, new_values: Dict[str, Any]
    ) -> NamedTuple:
        t_dict = cls._namedtuple_to_dict(t)
        updated_dict = recursive_dict_update(t_dict, new_values)
        return cls._dict_to_namedtuple(updated_dict)
