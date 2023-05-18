import os
import sys
import argparse
import pathlib
import logging
import logging.config

import django
from django.conf import settings
from django.core.management import execute_from_command_line

from dae.__version__ import VERSION, RELEASE
from dae.utils.verbosity_configuration import VerbosityConfiguration


logger = logging.getLogger("wgpf")


def _add_gpf_instance_path(parser):
    parser.add_argument(
        "--gpf-instance", "--gpf", type=str,
        default=None,
        help="Path to GPF instance configuration file. If None, the tool "
        "will check the environment for a 'DAE_DB_DIR' environment variable "
        "and if the variable is set it will use it as a GPF instance dictory. "
        "If 'DAE_DB_DIR' environment variable is not set, then the current "
        "directory and all its parents will be searched for a GPF instance "
        "configuration file `gpf_instance.yaml`")


def _configure_init_subparser(subparsers):
    parser = subparsers.add_parser(
        "init",
        help="Initialize a GPF Development Web Server for a GPF instance")

    _add_gpf_instance_path(parser)

    parser.add_argument(
        "-f", "--force", default=False,
        action="store_true",
        help="ingore the state of the instance and re-init.")


def _add_host_port_group(parser):
    group = parser.add_argument_group(
        title="Specify GPF development server host and port")

    group.add_argument(
        "-H", "--host", type=str,
        default="0.0.0.0",
        help="The host IP address on which the GPF development server will "
        "listen for incoming connections.")

    group.add_argument(
        "-P", "--port", type=int,
        default=8000,
        help="The port on which the GPF development server will listen "
        "for incomming connections.")


def _configure_run_subparser(subparsers):
    parser = subparsers.add_parser(
        "run",
        help="Run a GPF Development Web Server for a GPF instance")
    _add_host_port_group(parser)
    _add_gpf_instance_path(parser)


def _init_flag(wgpf_instance):
    return pathlib.Path(wgpf_instance.dae_dir) / ".wgpf_init.flag"


def _check_is_initialized(wgpf_instance):
    if not os.path.exists(wgpf_instance.dae_dir):
        return False
    if _init_flag(wgpf_instance).exists():
        return True
    return False


def _run_init_command(wgpf_instance, **kwargs):
    force = kwargs.pop("force", False)
    if _check_is_initialized(wgpf_instance) and not force:
        logger.error(
            "GPF instance %s already initialized. If you need to re-init "
            "please use '--force' flag.", wgpf_instance.dae_dir)
        sys.exit(0)

    try:
        try:
            execute_from_command_line([
                "wgpf", "migrate",
                "--skip-checks",
            ])
        except SystemExit:
            if not force:
                raise

        try:
            execute_from_command_line([
                "wgpf", "createapplication",
                "public", "authorization-code",
                "--client-id", "gpfjs",
                "--name", "GPF development server",
                "--redirect-uris", "http://localhost:8000/datasets",
                "--skip-checks",
            ])
        except SystemExit:
            if not force:
                raise

    finally:
        _init_flag(wgpf_instance).touch()


def _run_run_command(wgpf_instance, **kwargs):
    if not _check_is_initialized(wgpf_instance):
        logger.error(
            "GPF instance %s should be initialized first. "
            "Running `wgpf init`...",
            wgpf_instance.dae_dir)
        _run_init_command(wgpf_instance, **kwargs)

    host = kwargs.get("host")
    port = kwargs.get("port")

    try:
        execute_from_command_line([
            "wgpf", "runserver", f"{host}:{port}",
            "--skip-checks",
        ])

    finally:
        pass


def cli(argv=None):
    """Provide CLI for development GPF web server management."""
    if argv is None:
        argv = sys.argv[:]

    desc = "GPF Development Web Server Management Tool"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--version", action="store_true", default=False,
        help="Prints GPF version and exists.")
    VerbosityConfiguration.set_argumnets(parser)

    commands_parser = parser.add_subparsers(
        dest="command", help="Command to execute")

    _configure_init_subparser(commands_parser)
    _configure_run_subparser(commands_parser)

    args = parser.parse_args(argv[1:])

    if args.version:
        print(f"GPF version: {VERSION} ({RELEASE})")
        sys.exit(0)
    command = args.command
    if command is None:
        logger.error("missing wgpf subcommand")
        parser.print_help()
        sys.exit(1)

    # pylint: disable=import-outside-toplevel
    from gpf_instance import gpf_instance
    wgpf_instance = gpf_instance.get_wgpf_instance(args.gpf_instance)
    logger.info("using GPF instance at %s", wgpf_instance.dae_dir)

    if command not in {"init", "run"}:
        logger.error("unknown subcommand %s used in `wgpf`", command)
        sys.exit(1)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wdae.gpfjs_settings")

    django.setup()
    settings.DISABLE_PERMISSIONS = True
    settings.STUDIES_EAGER_LOADING = True

    settings.DEFAULT_WDAE_DIR = os.path.join(
        wgpf_instance.dae_dir, "wdae")
    os.makedirs(settings.DEFAULT_WDAE_DIR, exist_ok=True)

    if args.verbose > 0:
        settings.LOGGING["handlers"]["console"]["level"] = logging.DEBUG
    logging.config.dictConfig(settings.LOGGING)

    logger.info("using wdae directory: %s", settings.DEFAULT_WDAE_DIR)

    if command == "init":
        _run_init_command(wgpf_instance, **vars(args))
    elif command == "run":
        _run_run_command(wgpf_instance, **vars(args))
