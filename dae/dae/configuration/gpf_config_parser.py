import os
import glob
import logging
import fsspec

import yaml
import toml

from box import Box

from typing import List, Any, Dict, Optional
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

    # def _validate_is_aggregator(self, constraint, field, value):
    #     "{'type': 'boolean'}"

    #     if constraint is not True:
    #         return
    #     if value not in AGGREGATOR_CLASS_DICT.keys() and \
    #             not value.startswith("join"):
    #         self._error(
    #             field, f"Invalid aggregator type supplied {value}"
    #         )
    #     join_regex = r"^join\(.+\)"
    #     if value.startswith("join") and \
    #             re.match(join_regex, value) is None:
    #         self._error(field, "Incorrect join aggregator format")


class GPFConfigParser:

    filetype_parsers: dict = {
        ".yaml": yaml.safe_load,
        ".yml": yaml.safe_load,
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
        with fsspec.open(filename, "r") as infile:
            return infile.read()

    @staticmethod
    def parse_and_interpolate(content: str, parser=yaml.safe_load) -> dict:
        interpol_vars = parser(content).get("vars", {})

        env_vars = {f"${key}": val for key, val in os.environ.items()}
        interpol_vars = {
            key: value % env_vars for key, value in interpol_vars.items()
        }
        interpol_vars.update(env_vars)

        try:
            interpolated_text = content % interpol_vars
        except KeyError as ex:
            raise ValueError(f"interpolation problems: {ex}")

        config = parser(interpolated_text)
        config.pop("vars", None)
        return config

    @classmethod
    def parse_and_interpolate_file(cls, filename: str) -> dict:
        try:
            ext = os.path.splitext(filename)[1]
            if ext not in cls.filetype_parsers:
                raise ValueError(f"unsupported file type: {filename}")
            parser = cls.filetype_parsers[ext]

            file_contents = cls._get_file_contents(filename)
            return cls.parse_and_interpolate(file_contents, parser)

        except Exception as ex:
            logger.error(f"problems parsing config file <{filename}>")
            logger.error(ex)
            raise ex

    @staticmethod
    def merge_config(
            config: Dict[str, Any],
            default_config: Dict[str, Any] = None) -> Dict[str, Any]:
        if default_config is not None:
            config = recursive_dict_update(default_config, config)
        return config

    @staticmethod
    def validate_config(
            config: Dict[str, Any],
            schema: dict,
            conf_dir: str = None) -> dict:

        if conf_dir is not None and "conf_dir" in schema:
            config["conf_dir"] = conf_dir

        validator = GPFConfigValidator(
            schema, conf_dir=conf_dir
        )
        if not validator.validate(config):
            if conf_dir:
                raise ValueError(f"{conf_dir}: {validator.errors}")
            else:
                raise ValueError(f"{validator.errors}")
        return validator.document

    @staticmethod
    def process_config(
        config: Dict[str, Any],
        schema: dict,
        default_config: Dict[str, Any] = None,
        conf_dir: str = None,
    ) -> FrozenBox:

        config = GPFConfigParser.merge_config(config, default_config)
        config = GPFConfigParser.validate_config(config, schema, conf_dir)

        return FrozenBox(config)

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
        default_config_filename: Optional[str] = None,
        default_config: Optional[dict] = None,
    ) -> FrozenBox:

        if not os.path.exists(filename):
            raise ValueError(f"{filename} does not exist!")
        logger.debug(
            f"loading config {filename} with default configuration file "
            f"{default_config_filename};")

        config = cls.parse_and_interpolate_file(filename)
        if default_config_filename:
            assert default_config is None
            default_config = cls.parse_and_interpolate_file(
                default_config_filename)

        conf_dir = os.path.dirname(filename)
        return cls.process_config(
            config, schema, default_config, conf_dir)

    @classmethod
    def load_directory_configs(
            cls, dirname: str, schema: dict,
            default_config_filename: Optional[str] = None,
            default_config: Optional[dict] = None) -> List[Box]:
        return [
            cls.load_config(
                config_path, schema,
                default_config_filename=default_config_filename,
                default_config=default_config)
            for config_path in cls._collect_directory_configs(dirname)
        ]

    @classmethod
    def modify_tuple(
            cls, t: Box, new_values: Dict[str, Any]) -> Box:

        return FrozenBox(recursive_dict_update(t.to_dict(), new_values))
