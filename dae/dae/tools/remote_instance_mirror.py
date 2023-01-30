#!/usr/bin/env python
"""Tool to mirror remote GPF instances."""
import os
import re
import sys
import argparse
import subprocess
import logging
import copy

import yaml

from dae.impala_storage.helpers.rsync_helpers import RsyncHelpers


logger = logging.getLogger("remote_instance_mirror")


def parse_cli_arguments(argv):
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
        default=""
    )

    parser.add_argument(
        "--output",
        "-o",
        metavar="<output directory>",
        dest="output",
        help="output directory where to store the instance mirror",
        default="."
    )

    parser.add_argument(
        "--hdfs2nfs",
        metavar="<HDFS-to-NFS mount point>",
        dest="hdfs2nfs",
        help="HDFS-to-NFS mount point on remote host",
    )
    argv = parser.parse_args(argv)
    return argv


def load_mirror_config(filename):
    """Load mirrored instance configuration."""
    with open(filename, "rt", encoding="utf8") as infile:
        config = yaml.safe_load(infile)
    return config


def update_mirror_config(rsync_helpers, work_dir, argv):
    """Update mirrored GPF instance configuration."""
    config_filename = os.path.join(work_dir, "gpf_instance.yaml")
    config_dict = load_mirror_config(config_filename)

    config_dict["mirror_of"] = rsync_helpers.remote

    storage = copy.deepcopy(config_dict["storage"]["production_impala"])
    assert storage["storage_type"] == "impala"

    impala = storage["impala"]
    remote_impala_host = impala["hosts"][0]

    impala["hosts"] = ["localhost"]

    if "rsync" not in storage:
        assert argv.hdfs2nfs is not None, \
            "Please supply HDFS-to-NFS mount point in CLI arguments"
        hdfs2nfs = argv.hdfs2nfs
    else:
        hdfs2nfs = storage["rsync"]["location"]

    storage["rsync"] = {}
    storage["rsync"]["location"] = \
        f"{rsync_helpers.hosturl()}{hdfs2nfs}"

    config_dict["storage"]["genotype_impala"] = storage
    config_dict["genotype_storage"]["default"] = "genotype_impala"

    with open(config_filename, "wt", encoding="utf8") as outfile:
        content = yaml.dump(config_dict)
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


def get_active_conda_environment():
    """Detecst activate conda environment."""
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
    return None


def build_setenv(work_dir):
    """Prepare 'setenv.sh' script."""
    conda_environment = get_active_conda_environment()
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

conda activate {conda_environment}

PS1="({dirname}) $PS1"
export PS1

"""
    outfilename = os.path.join(work_dir, "setenv.sh")
    with open(outfilename, "wt", encoding="utf8") as outfile:
        outfile.write(content)


def run_wdae_bootstrap(work_dir):
    """Run wdae migrations and create default users."""
    os.environ["DAE_DB_DIR"] = work_dir
    commands = [
        [
            "wdaemanage.py", "migrate"  # NOSONAR
        ],
        [
            "wdaemanage.py", "user_create", "admin@iossifovlab.com",
            "-p", "secret", "-g", "any_dataset:admin"
        ],
        [
            "wdaemanage.py", "user_create", "research@iossifovlab.com",
            "-p", "secret"
        ]
    ]
    for command in commands:
        result = subprocess.run(
            command,
            text=True, capture_output=True, check=False)
        if result.returncode != 0:
            logger.error(" ".join(result.args))
            logger.error(result.stderr)


def main(argv):
    """Entry point for the remote instance mirroring tool."""
    argv = parse_cli_arguments(argv)

    if argv.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif argv.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif argv.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    logging.getLogger("impala").setLevel(logging.WARNING)

    rsync_helpers = RsyncHelpers(argv.remote_instance)

    output = argv.output
    if not output.endswith("/"):
        output += "/"
    output = os.path.abspath(output)

    os.makedirs(output, exist_ok=True)

    exclude = []
    if argv.exclude is not None:
        exclude = [ex.strip() for ex in argv.exclude.split(",")]
        exclude = [ex for ex in exclude if ex]

    rsync_helpers.copy_to_local(output, exclude=exclude)

    update_mirror_config(rsync_helpers, output, argv)
    build_setenv(output)
    run_wdae_bootstrap(output)


if __name__ == "__main__":
    main(sys.argv[1:])
