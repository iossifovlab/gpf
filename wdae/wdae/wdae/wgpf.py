import argparse
import logging
import logging.config
import os
import pathlib
import shutil
import sys
from typing import cast

import django
from dae.pheno.build_pheno_browser import main as build_pheno_browser
from dae.tools.generate_common_report import (
    main as generate_common_report,
)
from dae.tools.generate_denovo_gene_sets import (
    main as generate_denovo_gene_sets,
)
from dae.tools.reannotate_instance import ReannotateInstanceTool
from dae.utils.verbosity_configuration import VerbosityConfiguration
from django.conf import settings
from django.core.management import execute_from_command_line
from gpf_instance.gpf_instance import WGPFInstance

from dae import __version__  # type: ignore  # pylint: disable=C0412

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
        default="0.0.0.0",  # noqa: S104
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


def _init_flag(wgpf_instance: WGPFInstance) -> pathlib.Path:
    return pathlib.Path(wgpf_instance.dae_dir) / ".wgpf_init.flag"


def _check_is_initialized(wgpf_instance: WGPFInstance) -> bool:
    if not os.path.exists(wgpf_instance.dae_dir):
        return False
    return _init_flag(wgpf_instance).exists()


def _run_init_command(
        wgpf_instance: WGPFInstance, **kwargs: str | bool) -> None:
    force = cast(bool, kwargs.pop("force", False))
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


def _run_run_command(
        wgpf_instance: WGPFInstance, **kwargs: bool | str) -> None:
    if not _check_is_initialized(wgpf_instance):
        logger.info(
            "GPF instance %s should be initialized first. "
            "Running `wgpf init`...",
            wgpf_instance.dae_dir)
        _run_init_command(wgpf_instance, **kwargs)

    host = kwargs.get("host")
    port = kwargs.get("port")

    work_dir = os.path.join(
        wgpf_instance.dae_dir, ".reannotate-instance")
    shutil.rmtree(work_dir, ignore_errors=True)

    reannotation_tool = ReannotateInstanceTool(
        ["--work-dir", work_dir],
        gpf_instance=wgpf_instance)
    reannotation_tool.run()

    generate_denovo_gene_sets(
        [],
        gpf_instance=wgpf_instance,
    )
    generate_common_report(
        [],
        gpf_instance=wgpf_instance,
    )
    try:
        execute_from_command_line([
            "wgpf", "runserver", f"{host}:{port}",
            "--noreload",
            "--skip-checks",
        ])

    finally:
        pass


def cli(argv: list[str] | None = None) -> None:
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

    build_pheno_browser([
        "--gpf-instance",
        args.gpf_instance,
    ])

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wdae.wgpf_settings")
    if args.verbose == 1:
        settings.LOGGING[
            "handlers"]["console"]["level"] = logging.INFO  # type: ignore
    elif args.verbose >= 2:
        settings.LOGGING[
            "handlers"]["console"]["level"] = logging.DEBUG  # type: ignore
    logging.config.dictConfig(settings.LOGGING)

    django.setup()
    settings.DISABLE_PERMISSIONS = True
    settings.STUDIES_EAGER_LOADING = True

    # pylint: disable=import-outside-toplevel
    from gpf_instance import gpf_instance
    wgpf_instance = gpf_instance.get_wgpf_instance(args.gpf_instance)
    logger.info("using GPF instance at %s", wgpf_instance.dae_dir)

    if command not in {"init", "run"}:
        logger.error("unknown subcommand %s used in `wgpf`", command)
        sys.exit(1)

    settings.DEFAULT_WDAE_DIR = os.path.join(
        wgpf_instance.dae_dir, "wdae")
    os.makedirs(settings.DEFAULT_WDAE_DIR, exist_ok=True)

    logger.info("using wdae directory: %s", settings.DEFAULT_WDAE_DIR)

    if command == "init":
        _run_init_command(wgpf_instance, **vars(args))
    elif command == "run":
        _run_run_command(wgpf_instance, **vars(args))
