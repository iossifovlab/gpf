import argparse
import logging
import logging.config
import os
import sys
from typing import Optional

import django
from django.conf import settings
from django.core import management

from dae import __version__  # type: ignore
from dae.utils.verbosity_configuration import VerbosityConfiguration

logger = logging.getLogger("wgpf")


def _add_gpf_instance_path(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--gpf-instance", "--gpf", type=str,
        default=None,
        help="Path to GPF instance configuration file. If None, the tool "
        "will check the environment for a 'DAE_DB_DIR' environment variable "
        "and if the variable is set it will use it as a GPF instance dictory. "
        "If 'DAE_DB_DIR' environment variable is not set, then the current "
        "directory and all its parents will be searched for a GPF instance "
        "configuration file `gpf_instance.yaml`")


def _configure_init_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "init",
        help="Initialize a GPF Development Web Server for a GPF instance")

    _add_gpf_instance_path(parser)

    parser.add_argument(
        "-f", "--force", default=False,
        action="store_true",
        help="ingore the state of the instance and re-init.")


def _add_host_port_group(parser: argparse.ArgumentParser) -> None:
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


def _configure_run_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "run",
        help="Run a GPF Development Web Server for a GPF instance")
    _add_host_port_group(parser)
    _add_gpf_instance_path(parser)


def _run_init_command() -> None:
    management.call_command("migrate", "--skip-checks")
    from oauth2_provider.models import get_application_model  # pylint: disable=C0415  # noqa: I001  # noqa: I001
    app_exists = get_application_model().objects.filter(client_id="gpfjs")
    if not app_exists:
        management.call_command(
            "createapplication",
            "public", "authorization-code",
            "--client-id", "gpfjs",
            "--name", "GPF development server",
            "--redirect-uris", "http://localhost:8000/datasets",
            "--skip-checks",
        )


def _run_run_command(host: Optional[str], port: Optional[str]) -> None:
    _run_init_command()
    management.call_command(
        "runserver", f"{host}:{port}", "--skip-checks",
    )


def cli(argv: Optional[list[str]] = None) -> None:
    """Provide CLI for development GPF web server management."""
    if argv is None:
        argv = sys.argv[:]

    desc = "GPF Development Web Server Management Tool"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--version", action="store_true", default=False,
        help="Prints GPF version and exists.")
    VerbosityConfiguration.set_arguments(parser)

    commands_parser = parser.add_subparsers(
        dest="command", help="Command to execute")

    _configure_init_subparser(commands_parser)
    _configure_run_subparser(commands_parser)

    args = parser.parse_args(argv[1:])

    if args.version:
        print(f"GPF version: {__version__}")
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
        _run_init_command()
    elif command == "run":
        _run_run_command(args.host, args.port)
