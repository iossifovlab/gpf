#!/usr/bin/env python
from dae.backends.impala.rsync_helpers import RsyncHelpers
import os
import re
import sys
import argparse
import toml
import subprocess


def parse_cli_arguments(argv):
    parser = argparse.ArgumentParser(
        description="mirrors remote GPF data instance",
        conflict_handler="resolve",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

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
    with open(filename, "rt") as infile:
        content = infile.read()
        config = toml.loads(content)
    return config


def update_mirror_config(rsync_helpers, work_dir, argv):
    # parsed_remote = urlparse(remote)

    config_filename = os.path.join(work_dir, "DAE.conf")
    config_dict = load_mirror_config(config_filename)

    config_dict["mirror_of"] = rsync_helpers.remote

    storage = config_dict["storage"]["genotype_impala"]
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

    with open(config_filename, "wt") as outfile:
        content = toml.dumps(config_dict)
        outfile.write(content)

    filename = os.path.join(work_dir, "remote_impala_port_mapping.txt")
    port_mapping_command = \
        f"ssh -L 21050:{remote_impala_host}:21050 " \
        f"{rsync_helpers.parsed_remote.netloc}"
    with open(filename, "wt") as outfile:
        outfile.write(port_mapping_command)
        outfile.write("\n")

    return config_dict


def get_active_conda_environment():
    result = subprocess.run(
        ["conda", "env", "list"],
        text=True, capture_output=True)
    assert result.returncode == 0, result

    stdout = result.stdout

    regexp = re.compile("^(?P<env>.+?)\s+(?P<active>\\*)\s+(?P<path>\\/.+$)")

    lines = [ln.strip() for ln in stdout.split("\n")]
    for line in lines:
        match = regexp.match(line)
        if match:
            return match.groupdict()["env"]
    return None


def build_setenv(work_dir):
    conda_environment = get_active_conda_environment()
    dirname = os.path.basename(work_dir)

    scores_hg19_dir = os.environ.get(
        "DAE_GENOMIC_SCORES_HG19", "<define this environment variable>")
    scores_hg38_dir = os.environ.get(
        "DAE_GENOMIC_SCORES_HG38", "<define this environment variable>")

    content = f"""
#!/bin/bash

export DAE_GENOMIC_SCORES_HG19={scores_hg19_dir}
export DAE_GENOMIC_SCORES_HG38={scores_hg38_dir}

export DAE_DB_DIR={work_dir}

conda activate {conda_environment}

PS1="({dirname}) $PS1"
export PS1

"""

    with open(os.path.join(work_dir, "setenv.sh"), "wt") as outfile:
        outfile.write(content)


def run_wdae_bootstrap(work_dir):

    os.environ["DAE_DB_DIR"] = work_dir
    commands = [
        [
            "wdaemanage.py", "migrate"
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
            text=True, capture_output=True)
        if result.returncode != 0:
            print(" ".join(result.args))
            print(result.stderr)


def main(argv=sys.argv[1:]):
    argv = parse_cli_arguments(argv)

    rsync_helpers = RsyncHelpers(argv.remote_instance)

    output = argv.output
    if not output.endswith("/"):
        output += "/"
    output = os.path.abspath(output)

    os.makedirs(output, exist_ok=True)

    rsync_helpers.copy_to_local(output)

    update_mirror_config(rsync_helpers, output, argv)
    build_setenv(output)
    run_wdae_bootstrap(output)


if __name__ == "__main__":
    main(sys.argv[1:])
