import os
import glob
import logging

import yaml
import toml

from box import Box

from typing import List, Any, Dict
from cerberus import Validator

from dae.utils.dict_utils import recursive_dict_update


logger = logging.getLogger(__name__)


def validate_existing_path(field: str, value: str, error):
    if not os.path.isabs(value):
        error(field, f"path <{value}> is not an absolute path!")
    if not os.path.exists(value):
        error(field, f"path <{value}> does not exist!")


def validate_path(field: str, value: str, error):
    if not os.path.isabs(value):
        error(field, f"path <{value}> is not an absolute path!")


class DefaultBox(Box):
    def __init__(self, *args, **kwargs):
        kwargs["default_box"] = True
        kwargs["default_box_attr"] = None
        kwargs["default_box_none_transform"] = False
        super(DefaultBox, self).__init__(*args, **kwargs)


class FrozenBox(DefaultBox):
    def __init__(self, *args, **kwargs):
        kwargs["frozen_box"] = True
        super(FrozenBox, self).__init__(*args, **kwargs)


class GPFConfigValidator(Validator):
    def _normalize_coerce_abspath(self, value: str) -> str:
        directory = self._config["conf_dir"]
        if directory is None:
            return value
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
    def interpolate_contents(cls, file_contents, ext):
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
        return config

    @classmethod
    def parse_config(cls, filename: str) -> dict:
        try:
            ext = os.path.splitext(filename)[1]
            assert ext in cls.filetype_parsers, \
                f"Unsupported filetype {filename}!"
            file_contents = cls._get_file_contents(filename)

            return cls.interpolate_contents(file_contents, ext)

        except Exception as ex:
            logger.error(f"problems parsing config file <{filename}>")
            logger.error(ex)
            raise ex

    @classmethod
    def process_config(
        cls,
        config: Dict[str, Any],
        schema: dict,
        default_config: Dict[str, Any] = None,
        config_filename: str = None,
    ) -> FrozenBox:
        conf_dir = os.path.dirname(config_filename) \
            if config_filename else None
        validator = GPFConfigValidator(
            schema, conf_dir=conf_dir
        )
        if default_config is not None:
            config = recursive_dict_update(default_config, config)
        assert validator.validate(config), (config_filename, validator.errors)
        return FrozenBox(validator.document)

    @classmethod
    def load_config_raw(cls, filename: str) -> Dict[str, Any]:
        ext = os.path.splitext(filename)[1]
        assert ext in cls.filetype_parsers, f"Unsupported filetype {filename}!"
        file_contents = cls._get_file_contents(filename)
        return cls.filetype_parsers[ext](file_contents)  # type: ignore

    @classmethod
    def load_config(
        cls,
        filename: str,
        schema: dict,
        default_config_filename: str = None
    ) -> FrozenBox:
        assert os.path.exists(filename), f"{filename} does not exist!"
        config = cls.parse_config(filename)
        default_config = None
        if default_config_filename:
            default_config = cls.parse_config(default_config_filename)
        return GPFConfigParser.process_config(
            config, schema, default_config, filename
        )

    @classmethod
    def load_directory_configs(
            cls, dirname: str, schema: dict,
            default_config_filename: str = None) -> List[Box]:
        return [
            cls.load_config(config_path, schema, default_config_filename)
            for config_path in cls._collect_directory_configs(dirname)
        ]

    @classmethod
    def modify_tuple(
            cls, t: Box, new_values: Dict[str, Any]) -> Box:

        return FrozenBox(recursive_dict_update(t.to_dict(), new_values))
