#!/usr/bin/env python
import os
import sys
import argparse
import toml

# from pprint import pprint

from urllib.parse import urlparse, urlunparse

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema


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


def update_mirror_config(remote, config_dict):
    # parsed_remote = urlparse(remote)

    storage = config_dict["storage"]["genotype_impala"]
    assert storage["storage_type"] == "impala"

    impala = storage["impala"]
    impala["hosts"] = ["localhost"]

    return config_dict


def main(argv=sys.argv[1:]):
    argv = parse_cli_arguments(argv)

    remote = argv.remote_instance
    if remote.endswith("/"):
        remote = remote[:-1]

    parsed_remote = urlparse(remote)
    rsync_remote = remote
    if parsed_remote.hostname:
        rsync_remote = f"{parsed_remote.hostname}:{parsed_remote.path}"
        if parsed_remote.username:
            rsync_remote = f"{parsed_remote.username}@{rsync_remote}"

    output = argv.output
    if not output.endswith("/"):
        output += "/"

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

    work_dir = os.path.join(
        output,
        os.path.basename(remote)
    )

    config_filename = os.path.join(work_dir, "DAE.conf")
    config_dict = load_mirror_config(config_filename)

    mirror_config_dict = update_mirror_config(remote, config_dict)

    with open(config_filename, "wt") as outfile:
        content = toml.dumps(mirror_config_dict)
        outfile.write(content)


if __name__ == "__main__":
    main(sys.argv[1:])
