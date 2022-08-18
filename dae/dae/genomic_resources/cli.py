"""Provides CLI for management of genomic resources repositories."""
import os
import sys
import logging
import argparse
import pathlib
from typing import Dict
from urllib.parse import urlparse

import yaml

from dae.dask.client_factory import DaskClient

from dae.__version__ import VERSION, RELEASE
from dae.genomic_resources.repository import \
    GR_CONF_FILE_NAME, \
    GR_CONTENTS_FILE_NAME, \
    GenomicResource, \
    ReadWriteRepositoryProtocol, \
    ManifestEntry, \
    parse_resource_id_version, \
    version_tuple_to_string
from dae.utils.verbosity_configuration import VerbosityConfiguration

from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.histogram import HistogramBuilder


logger = logging.getLogger(__file__)


def _add_repository_resource_parameters_group(parser, use_resource=True):

    group = parser.add_argument_group(title="Repository/Resource")
    group.add_argument(
        "-R", "--repository", type=str,
        default=None,
        help="URL to the genomic resources repository. If not specified "
        "the tool assumes a local file system repository and starts looking "
        "for .CONTENTS file from the current working directory up to the root "
        "directory. If found the directory is assumed for root repository "
        "directory; otherwise error is reported.")
    if use_resource:
        group.add_argument(
            "-r", "--resource", type=str,
            help="Specifies the resource whose manifest we want to rebuild. "
            "If not specified the tool assumes local filesystem repository "
            "and starts looking for 'genomic_resource.yaml' file from "
            "current working directory up to the root directory. If found "
            "the directory is assumed for a resource directory; otherwise "
            "error is reported.")


def _add_dry_run_and_force_parameters_group(parser):
    group = parser.add_argument_group(title="Force/Dry run")
    group.add_argument(
        "-n", "--dry-run", default=False, action="store_true",
        help="only checks if the manifest update is needed whithout "
        "actually updating it")
    group.add_argument(
        "-f", "--force", default=False,
        action="store_true",
        help="ignore resource state and rebuild manifest")


def _add_dvc_parameters_group(parser):
    group = parser.add_argument_group(title="DVC params")
    group.add_argument(
        "-d", "--with-dvc", default=True,
        action="store_true", dest="use_dvc",
        help="use '.dvc' files if present to get md5 sum of resource files "
        "(default)")
    group.add_argument(
        "-D", "--without-dvc", default=True,
        action="store_false", dest="use_dvc",
        help="calculate the md5 sum if necessary of resource files; "
        "do not use '.dvc' files to get md5 sum of resource files")


def _add_hist_parameters_group(parser):
    group = parser.add_argument_group(title="Histograms")
    group.add_argument(
        "--region-size", type=int, default=3_000_000,
        help="Number of records to process in parallel")


def _configure_list_subparser(subparsers):
    parser = subparsers.add_parser("list", help="List a GR Repo")
    parser.add_argument(
        "-R", "--repository", type=str,
        default=None,
        help="URL to the genomic resources repository")


def _run_list_command(proto, _args):
    for res in proto.get_all_resources():
        res_size = sum([fs for _, fs in res.get_manifest().get_files()])
        print(
            f"{res.get_type():20} {res.get_version_str():7s} "
            f"{len(list(res.get_manifest().get_files())):2d} {res_size:12d} "
            f"{res.get_id()}")


def _configure_repo_init_subparser(subparsers):
    parser = subparsers.add_parser(
        "repo-init", help="Initialize a directory to turn it into a GRR")

    _add_repository_resource_parameters_group(parser, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser)


def _run_repo_init_command(**kwargs):
    repository = kwargs.get("repository")
    if repository is None:
        repo_url = _find_directory_with_filename(GR_CONTENTS_FILE_NAME)
    else:
        repo_url = _find_directory_with_filename(
            GR_CONTENTS_FILE_NAME, repository)

    if repo_url is not None:
        logger.error(
            "current working directory is part of a GRR at %s", repo_url)
        sys.exit(1)

    if repository is None:
        cwd = pathlib.Path().absolute()
    else:
        cwd = pathlib.Path(repository).absolute()

    proto = _create_proto(str(cwd))
    proto.build_content_file()


def _configure_repo_manifest_subparser(subparsers):
    parser = subparsers.add_parser(
        "repo-manifest", help="Create/update manifests for whole GRR")

    _add_repository_resource_parameters_group(parser, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)


def _configure_resource_manifest_subparser(subparsers):
    parser = subparsers.add_parser(
        "resource-manifest", help="Create/update manifests for a resource")

    _add_repository_resource_parameters_group(parser)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)


def _configure_repo_hist_subparser(subparsers):
    parser_hist = subparsers.add_parser(
        "repo-histograms",
        help="Build the histograms for a resource")

    _add_repository_resource_parameters_group(parser_hist, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser_hist)
    _add_hist_parameters_group(parser_hist)

    DaskClient.add_arguments(parser_hist)


def _configure_resource_hist_subparser(subparsers):
    parser_hist = subparsers.add_parser(
        "resource-histograms",
        help="Build the histograms for a resource")

    _add_repository_resource_parameters_group(parser_hist)
    _add_dry_run_and_force_parameters_group(parser_hist)
    _add_hist_parameters_group(parser_hist)

    DaskClient.add_arguments(parser_hist)


def _configure_repo_repair_subparser(subparsers):
    parser = subparsers.add_parser(
        "repo-repair",
        help="Update/rebuild manifest and histograms whole GRR")
    _add_repository_resource_parameters_group(parser, use_resource=False)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    _add_hist_parameters_group(parser)

    DaskClient.add_arguments(parser)


def _configure_resource_repair_subparser(subparsers):
    parser = subparsers.add_parser(
        "resource-repair",
        help="Update/rebuild manifest and histograms for a resource")
    _add_repository_resource_parameters_group(parser)
    _add_dry_run_and_force_parameters_group(parser)
    _add_dvc_parameters_group(parser)
    _add_hist_parameters_group(parser)

    DaskClient.add_arguments(parser)


def collect_dvc_entries(
        proto: ReadWriteRepositoryProtocol,
        res: GenomicResource) -> Dict[str, ManifestEntry]:
    """Collect manifest entries defined by .dvc files."""
    result = {}
    manifest = proto.collect_resource_entries(res)
    for entry in manifest:
        if not entry.name.endswith(".dvc"):
            continue
        filename = entry.name[:-4]
        basename = os.path.basename(filename)

        if filename not in manifest:
            logger.warning(
                "filling manifest of <%s> with entry for <%s> based on "
                "dvc data only",
                res.resource_id, filename)

        with proto.open_raw_file(res, entry.name, "rt") as infile:
            content = infile.read()
            dvc = yaml.safe_load(content)
            for data in dvc["outs"]:
                if data["path"] == basename:
                    result[filename] = \
                        ManifestEntry(filename, data["size"], data["md5"])

    return result


def _do_resource_manifest_command(proto, res, dry_run, force, use_dvc):
    prebuild_entries = {}
    if use_dvc:
        prebuild_entries = collect_dvc_entries(proto, res)

    manifest_update = proto.check_update_manifest(res, prebuild_entries)
    if not bool(manifest_update):
        print(
            f"manifest of <{res.get_genomic_resource_id_version()}> "
            f"is up to date",
            file=sys.stderr)
    else:
        msg = \
            f"manifest of " \
            f"<{res.get_genomic_resource_id_version()}> " \
            f"should be updated; " \
            f"entries to update in manifest " \
            f"{sorted(manifest_update.entries_to_update)}"
        if manifest_update.entries_to_delete:
            msg = f"{msg}; " \
                f"entries to delete from manifest " \
                f"{sorted(manifest_update.entries_to_delete)}"
        print(msg, file=sys.stderr)

    if dry_run:
        return

    if force:
        print(
            f"building manifest for resource <{res.resource_id}>...",
            file=sys.stderr)
        manifest = proto.build_manifest(
            res, prebuild_entries)
        proto.save_manifest(res, manifest)

    elif bool(manifest_update):
        print(
            f"updating manifest for resource <{res.resource_id}>...",
            file=sys.stderr)
        manifest = proto.update_manifest(
            res, prebuild_entries)
        proto.save_manifest(res, manifest)


def _run_repo_manifest_command(proto, **kwargs):
    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    use_dvc = kwargs.get("use_dvc", True)

    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return

    for res in proto.get_all_resources():
        _do_resource_manifest_command(proto, res, dry_run, force, use_dvc)

    proto.build_content_file()


def _find_resource(proto, repo_url, **kwargs):
    resource_id = kwargs.get("resource")
    if resource_id is not None:
        res = proto.get_resource(resource_id)
    else:
        if urlparse(repo_url).scheme not in {"file", ""}:
            logger.error(
                "resource not specified but the repository URL %s "
                "is not local filesystem repository", repo_url)
            return None

        cwd = os.getcwd()
        resource_dir = _find_directory_with_filename(GR_CONF_FILE_NAME, cwd)
        if resource_dir is None:
            logger.error("Can't find resource starting from %s", cwd)
            return None

        rid_ver = os.path.relpath(resource_dir, repo_url)
        resource_id, version = parse_resource_id_version(rid_ver)

        res = proto.get_resource(
            resource_id,
            version_constraint=f"={version_tuple_to_string(version)}")
    return res


def _run_resource_manifest_command(proto, repo_url, **kwargs):
    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    use_dvc = kwargs.get("use_dvc", True)

    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return
    res = _find_resource(proto, repo_url, **kwargs)
    if res is None:
        logger.error("resource not found...")
        return
    _do_resource_manifest_command(proto, res, dry_run, force, use_dvc)


def _do_resource_hist_command(  # pylint: disable=too-many-arguments
        client, proto, res, dry_run, force, region_size):
    if res.get_type() not in {
            "position_score", "np_score", "allele_score"}:
        print(
            f"skip histograms update for {res.resource_id}; "
            f"not a score", file=sys.stderr)
        return
    builder = HistogramBuilder(res)
    if dry_run:
        builder.check_update()
        return

    if force:
        histograms = builder.build(
            client,
            region_size=region_size)
    else:
        histograms = builder.update(
            client,
            region_size=region_size)

    hist_out_dir = "histograms"
    logger.info("Saving histograms in %s", hist_out_dir)
    builder.save(histograms, hist_out_dir)
    proto.save_manifest(res, proto.update_manifest(res))


def _run_repo_hist_command(proto, region_size, **kwargs):
    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return

    dask_client = DaskClient.from_dict(kwargs)
    if dask_client is None:
        sys.exit(1)

    with dask_client as client:
        for res in proto.get_all_resources():
            _do_resource_hist_command(
                client, proto, res, dry_run, force, region_size)
    if not dry_run:
        proto.build_content_file()


def _run_resource_hist_command(proto, repo_url, region_size, **kwargs):
    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return

    res = _find_resource(proto, repo_url, **kwargs)
    if res is None:
        logger.error("unable to find resource...")
        return
    dask_client = DaskClient.from_dict(kwargs)
    if dask_client is None:
        sys.exit(1)

    with dask_client as client:
        _do_resource_hist_command(
            client, proto, res, dry_run, force, region_size)


def _run_repo_repair_command(proto, region_size, **kwargs):
    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    use_dvc = kwargs.get("use_dvc", True)

    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return

    dask_client = DaskClient.from_dict(kwargs)
    if dask_client is None:
        sys.exit(1)
    with dask_client as client:
        for res in proto.get_all_resources():
            _do_resource_manifest_command(
                proto, res, dry_run, force, use_dvc)
            _do_resource_hist_command(
                client, proto, res, dry_run, force, region_size)
    if not dry_run:
        proto.build_content_file()


def _run_resource_repair_command(proto, repo_url, region_size, **kwargs):
    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    use_dvc = kwargs.get("use_dvc", True)

    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return

    res = _find_resource(proto, repo_url, **kwargs)
    if res is None:
        logger.error("unable to find a resource")
        sys.exit(1)

    dask_client = DaskClient.from_dict(kwargs)
    if dask_client is None:
        sys.exit(1)

    with dask_client as client:
        _do_resource_manifest_command(
            proto, res, dry_run, force, use_dvc)
        _do_resource_hist_command(
            client, proto, res, dry_run, force, region_size)


def cli_manage(cli_args=None):
    """Provide CLI for repository management."""
    if not cli_args:
        cli_args = sys.argv[1:]

    desc = "Genomic Resource Repository Management Tool"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--version", action="store_true", default=False,
        help="Prints GPF version and exists.")
    VerbosityConfiguration.set_argumnets(parser)

    commands_parser = parser.add_subparsers(
        dest="command", help="Command to execute")

    _configure_list_subparser(commands_parser)
    _configure_repo_init_subparser(commands_parser)
    _configure_repo_manifest_subparser(commands_parser)
    _configure_resource_manifest_subparser(commands_parser)
    _configure_repo_hist_subparser(commands_parser)
    _configure_resource_hist_subparser(commands_parser)
    _configure_repo_repair_subparser(commands_parser)
    _configure_resource_repair_subparser(commands_parser)

    args = parser.parse_args(cli_args)
    if args.version:
        print(f"GPF version: {VERSION} ({RELEASE})")
        sys.exit(0)

    command, repo_url = args.command, args.repository
    if command == "repo-init":
        _run_repo_init_command(**vars(args))
        return

    if args.repository is None:
        repo_url = _find_directory_with_filename(GR_CONTENTS_FILE_NAME)
        if repo_url is None:
            logger.error(
                "Can't find repository starting from: %s", os.getcwd())
            sys.exit(1)
        print("working with repository:", repo_url)

    proto = _create_proto(repo_url)

    if command == "repo-manifest":
        _run_repo_manifest_command(proto, **vars(args))
    elif command == "resource-manifest":
        _run_resource_manifest_command(proto, repo_url, **vars(args))
    elif command == "repo-histograms":
        _run_repo_hist_command(proto, **vars(args))
    elif command == "resource-histograms":
        _run_resource_hist_command(proto, repo_url, **vars(args))
    elif command == "repo-repair":
        _run_repo_repair_command(proto, **vars(args))
    elif command == "resource-repair":
        _run_resource_repair_command(proto, repo_url, **vars(args))
    elif command == "list":
        _run_list_command(proto, args)
    else:
        logger.error(
            "Unknown command %s. The known commands are index, "
            "list and histogram", command)
        sys.exit(1)


def _create_proto(repo_url):
    if not os.path.isabs(repo_url):
        repo_url = os.path.abspath(repo_url)

    proto = build_fsspec_protocol(proto_id="manage", root_url=repo_url)
    if not isinstance(proto, ReadWriteRepositoryProtocol):
        raise ValueError(
            f"resource management works with RW protocols; "
            f"{proto.proto_id} ({proto.scheme}) is read only")
    return proto


def _find_directory_with_filename(filename, cwd=None):
    if cwd is None:
        cwd = pathlib.Path().absolute()
    else:
        cwd = pathlib.Path(cwd).absolute()

    pathname = cwd / filename
    if pathname.exists():
        return str(cwd)

    for work_dir in cwd.parents:
        pathname = work_dir / filename
        if pathname.exists():
            return str(work_dir)

    return None
