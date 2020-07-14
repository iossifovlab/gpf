#!/usr/bin/env python
import os
import re
import sys
import argparse
import toml
import subprocess

# from pprint import pprint

from urllib.parse import urlparse


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
    argv = parser.parse_args(argv)
    return argv


def load_mirror_config(filename):
    with open(filename, "rt") as infile:
        content = infile.read()
        config = toml.loads(content)
    return config


def update_mirror_config(remote, work_dir):
    # parsed_remote = urlparse(remote)

    config_filename = os.path.join(work_dir, "DAE.conf")
    config_dict = load_mirror_config(config_filename)

    storage = config_dict["storage"]["genotype_impala"]
    assert storage["storage_type"] == "impala"

    impala = storage["impala"]
    impala["hosts"] = ["localhost"]

    with open(config_filename, "wt") as outfile:
        content = toml.dumps(config_dict)
        outfile.write(content)

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

    content = f"""
export DAE_DB_DIR={work_dir}

conda activate {conda_environment}

PS1="({dirname}) $PS1"
export PS1

"""

    with open(os.path.join(work_dir, "setenv.sh"), "wt") as outfile:
        outfile.write(content)


def build_wdae_bootstrap(work_dir):

    content = f"""
#!/bin/bash

wdaemanage.py migrate
wdaemanage.py user_create admin@iossifovlab.com -p secret -g any_dataset:admin
wdaemanage.py user_create research@iossifovlab.com -p secret

"""

    with open(os.path.join(work_dir, "wdae_bootstrap.sh"), "wt") as outfile:
        outfile.write(content)


def main(argv=sys.argv[1:]):
    argv = parse_cli_arguments(argv)

    remote = argv.remote_instance
    if not remote.endswith("/"):
        remote += "/"

    parsed_remote = urlparse(remote)
    rsync_remote = remote
    if parsed_remote.hostname:
        rsync_remote = f"{parsed_remote.hostname}:{parsed_remote.path}"
        if parsed_remote.username:
            rsync_remote = f"{parsed_remote.username}@{rsync_remote}"

    output = argv.output
    if not output.endswith("/"):
        output += "/"
    output = os.path.abspath(output)

    os.makedirs(output, exist_ok=True)

    exclude = argv.exclude.split(",")
    exclude.extend([
        "wdae/*",
        "import_data",
        ".dvc",
        ".git",
        ".gitignore",
    ])
    exclude = [f"--exclude {ex}" for ex in exclude if ex]

    command = ["rsync", "-avPHtb", rsync_remote, output]
    command.extend(exclude)

    command = " ".join(command)
    print(command)
    os.system(command)

    update_mirror_config(remote, output)
    build_setenv(output)
    build_wdae_bootstrap(output)


if __name__ == "__main__":
    main(sys.argv[1:])
