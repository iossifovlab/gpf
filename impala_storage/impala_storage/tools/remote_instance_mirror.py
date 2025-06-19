#!/usr/bin/env python
"""Tool to mirror remote GPF instances."""
import argparse
import copy
import logging
import os
import re
import subprocess
import sys
from typing import Any, cast

import yaml
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)

from impala_storage.helpers.rsync_helpers import RsyncHelpers

logger = logging.getLogger("remote_instance_mirror")


def parse_cli_arguments(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="mirrors remote GPF data instance",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--verbose", "-V", action="count", default=0)

    parser.add_argument(
        "remote_instance",
        type=str,
        metavar="<remote_instance>",
        help="remote instance location",
    )

    parser.add_argument(
        "--remote-shell",
        "-e",
        type=str,
        metavar="<remote shell>",
        dest="remote_shell",
        help="remote shell specification if needed"
        "[default: %(default)s]",
        default=None,
    )

    parser.add_argument(
        "--exclude",
        metavar="<exclude pattern>",
        dest="exclude",
        help="comma-separated list of exclude patterns",
        default="",
    )

    parser.add_argument(
        "--output",
        "-o",
        metavar="<output directory>",
        dest="output",
        help="output directory where to store the instance mirror",
        default=".",
    )

    parser.add_argument(
        "--hdfs2nfs",
        metavar="<HDFS-to-NFS mount point>",
        dest="hdfs2nfs",
        help="HDFS-to-NFS mount point on remote host",
    )
    return parser.parse_args(argv)


def load_mirror_config(filename: str) -> dict[str, Any]:
    """Load mirrored instance configuration."""
    with open(filename, "rt", encoding="utf8") as infile:
        config = yaml.safe_load(infile)
    return cast(dict[str, Any], config)


def update_genotype_storage_config(
    config_dict: dict[str, Any],
    rsync_helpers: RsyncHelpers,
    **kwargs: Any,
) -> str:
    """Update default genotype storage config."""
    storage_registry = GenotypeStorageRegistry()
    storage_registry.register_storages_configs(config_dict["genotype_storage"])
    default_storage = storage_registry.get_default_genotype_storage()
    if default_storage is None:
        raise ValueError("default genotype storage not configured")
    if default_storage.storage_type != "impala":
        raise ValueError("this works only for impala storage")
    storage = copy.deepcopy(default_storage.storage_config)

    impala = storage["impala"]
    remote_impala_host = impala["hosts"][0]

    impala["hosts"] = ["localhost"]

    if "rsync" not in storage:
        assert kwargs.get("hdfs2nfs") is not None, \
            "Please supply HDFS-to-NFS mount point in CLI arguments"
        hdfs2nfs = kwargs.get("hdfs2nfs")
    else:
        hdfs2nfs = storage["rsync"]["location"]

    storage["rsync"] = {}
    storage["rsync"]["location"] = \
        f"{rsync_helpers.hosturl()}{hdfs2nfs}"

    for index, storage_config in enumerate(
            config_dict["genotype_storage"]["storages"]):
        if storage_config["id"] == default_storage.storage_id:
            config_dict["genotype_storage"]["storages"][index] = storage

    return cast(str, remote_impala_host)


def update_mirror_config(
    rsync_helpers: RsyncHelpers,
    work_dir: str,
    argv: argparse.Namespace,
) -> dict[str, Any]:
    """Update mirrored GPF instance configuration."""
    config_filename = os.path.join(work_dir, "gpf_instance.yaml")
    config_dict = load_mirror_config(config_filename)

    config_dict["mirror_of"] = rsync_helpers.remote

    remote_impala_host = update_genotype_storage_config(
        config_dict, rsync_helpers, **vars(argv))

    with open(config_filename, "wt", encoding="utf8") as outfile:
        content = yaml.dump(config_dict, sort_keys=False)
        outfile.write(content)

    filename = os.path.join(work_dir, "remote_impala_port_mapping.txt")
    logger.debug("remote netloc: %s", rsync_helpers.parsed_remote)
    port_mapping_command = \
        f"ssh -L 21050:{remote_impala_host}:21050 " \
        f"{rsync_helpers.parsed_remote.netloc}"
    with open(filename, "wt", encoding="utf8") as outfile:
        outfile.write(port_mapping_command)
        outfile.write("\n")

    return config_dict


def get_active_conda_environment() -> str | None:
    """Detect activate conda environment."""
    try:
        result = subprocess.run(
            ["conda", "env", "list"],
            text=True, capture_output=True, check=True)
        assert result.returncode == 0, result

        stdout = result.stdout

        regexp = re.compile(
            "^(?P<env>.+?)\\s+(?P<active>\\*)\\s+(?P<path>\\/.+$)")

        lines = [ln.strip() for ln in stdout.split("\n")]
        for line in lines:
            match = regexp.match(line)
            if match:
                return match.groupdict()["env"]
    except Exception:  # pylint: disable=broad-except
        logger.warning("unable to detect conda environment", exc_info=True)
    return None


def build_setenv(work_dir: str) -> None:
    """Prepare 'setenv.sh' script."""
    conda_environment = get_active_conda_environment()
    conda_activate = ""
    if conda_environment:
        conda_activate = f"conda activate {conda_environment}"

    dirname = os.path.basename(work_dir)

    grr_definition = os.environ.get(
        "GRR_DEFINITION", "<define this environment variable>")

    gpf_prefix = os.environ.get("GPF_PREFIX", "gpfjs")

    content = f"""
#!/bin/bash

export GRR_DEFINITION={grr_definition}

export DAE_DB_DIR={work_dir}
export DAE_PHENODB_DIR={work_dir}

export GPF_PREFIX={gpf_prefix}

{conda_activate}

PS1="({dirname}) $PS1"
export PS1

"""
    outfilename = os.path.join(work_dir, "setenv.sh")
    with open(outfilename, "wt", encoding="utf8") as outfile:
        outfile.write(content)


def run_wdae_bootstrap(work_dir: str) -> None:
    """Run wdae migrations and create default users."""
    os.environ["DAE_DB_DIR"] = work_dir
    commands = [
        [
            "wdaemanage.py", "migrate",  # NOSONAR
        ],
        [
            "wdaemanage.py", "user_create", "admin@iossifovlab.com",
            "-p", "secret", "-g", "any_dataset:admin",
        ],
        [
            "wdaemanage.py", "user_create", "research@iossifovlab.com",
            "-p", "secret",
        ],
    ]
    for command in commands:
        result = subprocess.run(
            command,
            text=True, capture_output=True, check=False)
        if result.returncode != 0:
            logger.error(" ".join(result.args))
            logger.error(result.stderr)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the remote instance mirroring tool."""
    if argv is None:
        argv = sys.argv[1:]

    args = parse_cli_arguments(argv)

    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    logging.getLogger("impala").setLevel(logging.WARNING)

    rsync_helpers = RsyncHelpers(args.remote_instance)

    output = args.output
    if not output.endswith("/"):
        output += "/"
    output = os.path.abspath(output)

    os.makedirs(output, exist_ok=True)

    exclude = []
    if args.exclude is not None:
        exclude = [ex.strip() for ex in args.exclude.split(",")]
        exclude = [ex for ex in exclude if ex]

    rsync_helpers.copy_to_local(output, exclude=exclude)

    update_mirror_config(rsync_helpers, output, args)
    build_setenv(output)
    run_wdae_bootstrap(output)
