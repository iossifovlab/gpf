from __future__ import annotations

import glob
import logging
import os
from collections.abc import Callable
from copy import deepcopy
from typing import Any, ClassVar, cast

import fsspec
import toml
import yaml
from box import Box
from cerberus import Validator

from dae.utils.dict_utils import recursive_dict_update

logger = logging.getLogger(__name__)


class DefaultBox(Box):
    # pylint: disable=too-few-public-methods
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["default_box"] = True
        kwargs["default_box_attr"] = None
        kwargs["default_box_none_transform"] = False
        super().__init__(*args, **kwargs)


class FrozenBox(DefaultBox):
    # pylint: disable=too-few-public-methods
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["frozen_box"] = True
        super().__init__(*args, **kwargs)


class GPFConfigValidator(Validator):
    """
    Validator class with various extra cerberus features for GPF.

    Supports:
        "coerce": "abspath" - transform a relative path in configuration
        to an absolute path
    """

    def _validate_depends_global(
            self, constraint: str,
            field: str, value: Any) -> None:
        # pylint: disable=unused-argument
        """
        Check if a given other value exists anywhere in the dictionary.

        Will also validate if the value of the target is False
        The rule's arguments are validated against this schema:
        {"type": "string"}
        """
        if isinstance(value, bool) and value is False:
            return

        field_path = constraint.split(".")
        current_parent = self.root_document  # pyright: ignore
        failed_to_find = False
        for field_name in field_path:
            next_field = current_parent.get(field_name, None)
            if next_field is None:
                failed_to_find = True
                break
            current_parent = next_field

        if failed_to_find:
            self._error(  # pyright: ignore
                field, f"Depends on {constraint}, which is missing!")

    def _normalize_coerce_abspath(self, value: str) -> str:
        directory = self._config["conf_dir"]  # pyright: ignore
        if directory is None:
            return value
        if not os.path.isabs(value):
            value = os.path.join(directory, value)
        return os.path.normpath(value)


class GPFConfigParser:
    """
    Class that handles reading, validation and parsing of all GPF config files.

    Supports loading from YAML and TOML files.
    Parsing used depends on type specified in filename:
        .yaml, .yml - YAML parse
        .toml, .conf - TOML parse

    """

    filetype_parsers: ClassVar[dict[str, Any]] = {
        ".yaml": yaml.safe_load,
        ".yml": yaml.safe_load,
        # ".json": json.loads,
        ".toml": toml.loads,
        ".conf": toml.loads,
    }

    @classmethod
    def collect_directory_configs(cls, dirname: str) -> list[str]:
        """Collect all config files in a directory."""
        config_files: list[str] = []
        for filetype in cls.filetype_parsers:
            config_files += glob.glob(
                os.path.join(dirname, f"**/*{filetype}"), recursive=True,
            )
        return config_files

    @classmethod
    def _get_file_contents(cls, filename: str | os.PathLike) -> str:
        with fsspec.open(filename, "r") as infile:
            return cast(str, infile.read())  # pyright: ignore

    @staticmethod
    def parse_and_interpolate(
            content: str, parser: Callable[[str], dict] = yaml.safe_load,
            conf_dir: str | None = None) -> dict:
        """Parse text content and perform variable interpolation on result."""
        parsed_content = parser(content) or {}
        interpol_vars = parsed_content.get("vars") or {}
        assert interpol_vars is not None

        env_vars = {f"${key}": val for key, val in os.environ.items()}
        interpol_vars = {
            key: value % env_vars for key, value in interpol_vars.items()
        }
        interpol_vars.update(env_vars)
        if conf_dir:
            interpol_vars.update({
                "conf_dir": conf_dir,
                "wd": conf_dir,
                "work_dir": conf_dir,
            })

        try:
            interpolated_text = content % interpol_vars
        except KeyError as ex:
            raise ValueError(f"interpolation problems: {ex}") from ex

        config = parser(interpolated_text) or {}
        config.pop("vars", None)
        return config

    @classmethod
    def parse_and_interpolate_file(
        cls, filename: str | os.PathLike,
        conf_dir: str | None = None,
    ) -> dict:
        """Open a file and interpolate it's contents."""
        try:
            ext = os.path.splitext(filename)[1]
            if ext not in cls.filetype_parsers:
                raise ValueError(  # noqa: TRY301
                    f"unsupported file type: {filename}")
            parser = cls.filetype_parsers[ext]

            file_contents = cls._get_file_contents(filename)
            if conf_dir is None:
                conf_dir = os.path.abspath(os.path.dirname(filename))
            return cls.parse_and_interpolate(
                file_contents, parser, conf_dir=conf_dir)

        except Exception:
            logger.exception("problems parsing config file <%s>", filename)
            raise

    @staticmethod
    def merge_config(
            config: dict[str, Any],
            default_config: dict[str, Any] | None = None) -> dict[str, Any]:
        if default_config is not None:
            config = recursive_dict_update(default_config, config)
        return config

    @staticmethod
    def validate_config(
        config: dict[str, Any],
        schema: dict,
        conf_dir: str | None = None,
    ) -> dict:
        """Perform validation on a parsed config."""
        if conf_dir is not None and "conf_dir" in schema:
            config["conf_dir"] = conf_dir

        # This is done because cerberus validators may perform
        # in-place edits to the schema,
        # potentially resulting in inconsistent behavior
        schema_copy = deepcopy(schema)

        validator = GPFConfigValidator(
            schema_copy, conf_dir=conf_dir,  # pyright: ignore
        )
        if not validator.validate(config):  # pyright: ignore
            if conf_dir:
                raise ValueError(
                    f"{conf_dir}: {validator.errors}")  # pyright: ignore

            raise ValueError(f"{validator.errors}")  # pyright: ignore
        return cast(dict, validator.document)  # pyright: ignore

    @staticmethod
    def process_config_raw(
        config: dict[str, Any],
        schema: dict,
        default_config: dict[str, Any] | None = None,
        conf_dir: str | None = None,
    ) -> dict:
        """
        Pass an interpolated config to validation and prepare it for use.

        default_config: interpolated configuration to use for defaults where
        values in the main configuration are missing.
        """
        config = GPFConfigParser.merge_config(config, default_config)
        return GPFConfigParser.validate_config(config, schema, conf_dir)

    @staticmethod
    def process_config(
        config: dict[str, Any],
        schema: dict,
        default_config: dict[str, Any] | None = None,
        conf_dir: str | None = None,
    ) -> Box:
        """
        Pass an interpolated config to validation and prepare it for use.

        default_config: interpolated configuration to use for defaults where
        values in the main configuration are missing.
        """
        config = GPFConfigParser.merge_config(config, default_config)
        config = GPFConfigParser.validate_config(config, schema, conf_dir)

        return cast(Box, DefaultBox(config))

    @classmethod
    def load_config_raw(cls, filename: str) -> dict[str, Any]:
        ext = os.path.splitext(filename)[1]
        assert ext in cls.filetype_parsers, f"Unsupported filetype {filename}!"
        file_contents = cls._get_file_contents(filename)
        return cls.filetype_parsers[ext](file_contents)  # type: ignore

    @classmethod
    def load_config(
        cls,
        filename: str,
        schema: dict,
        default_config_filename: str | None = None,
        default_config: dict | None = None,
    ) -> Box:
        """Load a file and return a processed configuration."""
        if not os.path.exists(filename):
            raise ValueError(f"{filename} does not exist!")
        logger.debug(
            "loading config %s with default configuration file %s;",
            filename, default_config_filename)

        try:
            config = cls.parse_and_interpolate_file(filename)
            if default_config_filename:
                assert default_config is None
                default_config = cls.parse_and_interpolate_file(
                    default_config_filename)

            conf_dir = os.path.abspath(os.path.dirname(filename))
            return cls.process_config(
                config, schema, default_config, conf_dir)
        except ValueError:
            logger.exception(
                "unable to parse configuration: %s with default config %s "
                "(%s) and schema %s", filename,
                default_config_filename, default_config, schema)
            raise

    @classmethod
    def load_config_dict(
        cls,
        filename: str,
        schema: dict,
        default_config_filename: str | None = None,
        default_config: dict | None = None,
    ) -> dict:
        """Load a file and return a processed configuration."""
        if not os.path.exists(filename):
            raise ValueError(f"{filename} does not exist!")
        logger.debug(
            "loading config %s with default configuration file %s;",
            filename, default_config_filename)

        try:
            config = cls.parse_and_interpolate_file(filename)
            if default_config_filename:
                assert default_config is None
                default_config = cls.parse_and_interpolate_file(
                    default_config_filename)

            conf_dir = os.path.abspath(os.path.dirname(filename))
            return cls.process_config_raw(
                config, schema, default_config, conf_dir)
        except ValueError:
            logger.exception(
                "unable to parse configuration: %s with default config %s "
                "(%s) and schema %s", filename,
                default_config_filename, default_config, schema)
            raise

    @classmethod
    def load_directory_configs(
            cls, dirname: str, schema: dict,
            default_config_filename: str | None = None,
            default_config: dict | None = None) -> list[Box]:
        """Find and load all configs in a given root directory."""
        result = []
        for config_path in cls.collect_directory_configs(dirname):
            if config_path.endswith((".conf", ".toml")):
                logger.warning(
                    "TOML configurations have been deprecated - %s",
                    config_path,
                )
            try:
                config = cls.load_config(
                    config_path, schema,
                    default_config_filename=default_config_filename,
                    default_config=default_config)

                result.append(config)

            except ValueError:
                logger.exception(
                    "unable to parse configuration file %s; skipped",
                    config_path)

        return result

    @classmethod
    def modify_tuple(
            cls, tup: Box, new_values: dict[str, Any]) -> Box:

        return FrozenBox(recursive_dict_update(tup.to_dict(), new_values))
