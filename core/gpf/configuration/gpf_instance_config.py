"""Discovery and loading of the top-level GPF instance configuration.

This lives in the low-level ``configuration`` package (rather than on
``GPFInstance``) so that other core modules — notably ``gpf.pheno`` — can
resolve the instance config without importing ``gpf.gpf_instance``, which
would create an import cycle (``gpf_instance`` imports ``pheno``).
"""
from __future__ import annotations

import os
from pathlib import Path

from box import Box
from gain.utils.fs_utils import find_directory_with_a_file

from gpf.configuration.gpf_config_parser import GPFConfigParser
from gpf.configuration.schemas.dae_conf import dae_conf_schema


def build_gpf_config(
    config_filename: str | Path | None = None,
) -> tuple[Box, Path, Path]:
    """Build GPF config from a config file or environment variable.

    When ``config_filename`` is ``None``, the instance is discovered via
    ``GPF_CONF_DIR``, then ``DAE_DB_DIR``, then a walk of the current
    directory and its parents for a ``gpf_instance.yaml``.
    """
    dae_dir: Path | None
    if config_filename is not None:
        config_filename = Path(config_filename)
        dae_dir = config_filename.parent
    else:
        if os.environ.get("GPF_CONF_DIR"):
            dae_dir = Path(os.environ["GPF_CONF_DIR"])
            config_filename = Path(dae_dir) / "gpf_instance.yaml"
        elif os.environ.get("DAE_DB_DIR"):
            dae_dir = Path(os.environ["DAE_DB_DIR"])
            config_filename = Path(dae_dir) / "gpf_instance.yaml"
        else:
            dae_dir = find_directory_with_a_file("gpf_instance.yaml")
            if dae_dir is None:
                raise ValueError("unable to locate GPF instance directory")
            config_filename = dae_dir / "gpf_instance.yaml"
    assert config_filename is not None
    if not config_filename.exists():
        raise ValueError(
            f"GPF instance config <{config_filename}> does not exists")
    dae_config = GPFConfigParser.load_config(
        str(config_filename), dae_conf_schema)
    return dae_config, dae_dir, config_filename
