"""Provides CLI for management of genomic resources repositories."""
import os
import sys
import logging
import argparse
from typing import Dict

import yaml

from dae.dask.client_factory import DaskClient

from dae.__version__ import VERSION, RELEASE
from dae.genomic_resources.repository import \
    GenomicResource, \
    ReadWriteRepositoryProtocol, \
    ManifestEntry
from dae.utils.verbosity_configuration import VerbosityConfiguration

from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.histogram import HistogramBuilder


logger = logging.getLogger(__file__)


def _configure_hist_subparser(subparsers):
    parser_hist = subparsers.add_parser("histogram",
                                        help="Build the histograms \
                                        for a resource")
    parser_hist.add_argument(
        "repo_url", type=str,
        help="Path to the genomic resources repository")
    parser_hist.add_argument("-r", "--resource", type=str,
                             help="resource to generate histograms for")

    VerbosityConfiguration.set_argumnets(parser_hist)
    parser_hist.add_argument("--region-size", type=int, default=3_000_000,
                             help="Number of records to process in parallel")
    parser_hist.add_argument("-f", "--force", default=False,
                             action="store_true", help="Ignore histogram "
                             "hashes and always precompute all histograms")
    parser_hist.add_argument(
        "-n", "--dry-run", default=False, action="store_true",
        help="only checks if the histograms update is needed whithout "
        "actually updating it")
    DaskClient.add_arguments(parser_hist)


def _configure_list_subparser(subparsers):
    parser_list = subparsers.add_parser("list", help="List a GR Repo")
    parser_list.add_argument(
        "repo_url", type=str,
        help="Path to the genomic resources repository")
    VerbosityConfiguration.set_argumnets(parser_list)


def _run_list_command(proto, _args):
    for res in proto.get_all_resources():
        res_size = sum([fs for _, fs in res.get_manifest().get_files()])
        print(
            f"{res.get_type():20} {res.get_version_str():7s} "
            f"{len(list(res.get_manifest().get_files())):2d} {res_size:12d} "
            f"{res.get_id()}")


def _configure_manifest_subparser(subparsers):
    parser_manifest = subparsers.add_parser(
        "manifest", help="Create manifest for a resource")
    VerbosityConfiguration.set_argumnets(parser_manifest)
    parser_manifest.add_argument(
        "repo_url", type=str,
        help="Path to the genomic resources repository")
    parser_manifest.add_argument(
        "-r", "--resource", type=str,
        help="specifies a resource whose manifest we want to rebuild")
    parser_manifest.add_argument(
        "-n", "--dry-run", default=False, action="store_true",
        help="only checks if the manifest update is needed whithout "
        "actually updating it")
    parser_manifest.add_argument(
        "-f", "--force", default=False,
        action="store_true",
        help="ignore resource state and rebuild manifest")

    parser_manifest.add_argument(
        "-d", "--with-dvc", default=True,
        action="store_true", dest="use_dvc",
        help="use '.dvc' files if present to get md5 sum of resource files")
    parser_manifest.add_argument(
        "-D", "--without-dvc", default=True,
        action="store_false", dest="use_dvc",
        help="calculate the md5 sum if necessary of resource files; "
        "do not use '.dvc' files to get md5 sum of resource files")


def _configure_repair_subparser(subparsers):
    parser = subparsers.add_parser(
        "repair", help="Update/rebuild manifest and histograms for a resource")
    VerbosityConfiguration.set_argumnets(parser)
    parser.add_argument(
        "repo_url", type=str,
        help="Path to the genomic resources repository")
    parser.add_argument(
        "-r", "--resource", type=str,
        help="specifies a resource whose manifest/histograms we want "
        "to rebuild; if not specified the command will run on all "
        "resources in the repository")
    parser.add_argument(
        "-n", "--dry-run", default=False, action="store_true",
        help="only checks if the manifest and/or histograms update is "
        "needed whithout actually updating it")
    parser.add_argument(
        "-f", "--force", default=False,
        action="store_true",
        help="ignore resource state and rebuild manifest and histograms")

    parser.add_argument(
        "-d", "--with-dvc", default=True,
        action="store_true", dest="use_dvc",
        help="use '.dvc' files if present to get md5 sum of resource files")
    parser.add_argument(
        "-D", "--without-dvc", default=True,
        action="store_false", dest="use_dvc",
        help="calculate the md5 sum if necessary of resource files; "
        "do not use '.dvc' files to get md5 sum of resource files")

    parser.add_argument(
        "--region-size", type=int, default=3_000_000,
        help="split the resource into regions with region length for "
        "parallel processing")

    DaskClient.add_arguments(parser)


def _get_resources_list(proto, **kwargs):
    res_id = kwargs.get("resource")
    if res_id is not None:
        res = proto.find_resource(res_id)
        if res is None:
            logger.error(
                "resource %s not found in repository %s",
                res_id, proto.url)
            sys.exit(1)
        resources = [res]
    else:
        resources = list(proto.get_all_resources())
    return resources


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


def _run_resource_manifest_command(proto, res, dry_run, force, use_dvc):
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
            f"{manifest_update.entries_to_update}"
        if manifest_update.entries_to_delete:
            msg = f"{msg}; " \
                f"entries to delete from manifest " \
                f"{manifest_update.entries_to_delete}"
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


def _run_manifest_command(proto, **kwargs):
    resources = _get_resources_list(proto, **kwargs)

    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    use_dvc = kwargs.get("use_dvc", True)

    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return

    for res in resources:
        _run_resource_manifest_command(proto, res, dry_run, force, use_dvc)

    proto.build_content_file()


def _run_resource_hist_command(  # pylint: disable=too-many-arguments
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
    proto.update_manifest(res)


def _run_hist_command(proto, region_size, **kwargs):
    resources = _get_resources_list(proto, **kwargs)

    dry_run = kwargs.get("dry_run", False)
    force = kwargs.get("force", False)
    if dry_run and force:
        logger.warning("please choose one of 'dry_run' and 'force' options")
        return

    dask_client = DaskClient.from_dict(kwargs)
    if dask_client is None:
        sys.exit(1)

    with dask_client as client:
        for res in resources:
            _run_resource_hist_command(
                client, proto, res, dry_run, force, region_size)
    proto.build_content_file()


def _run_repair_command(proto, region_size, **kwargs):
    resources = _get_resources_list(proto, **kwargs)

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
        for res in resources:
            _run_resource_manifest_command(
                proto, res, dry_run, force, use_dvc)
            _run_resource_hist_command(
                client, proto, res, dry_run, force, region_size)
    proto.build_content_file()


def cli_manage(cli_args=None):
    """Provide CLI for repository management."""
    if not cli_args:
        cli_args = sys.argv[1:]

    desc = "Genomic Resource Repository Management Tool"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--version", action="store_true", default=False,
        help="Prints GPF version and exists.")
    subparsers = parser.add_subparsers(dest="command",
                                       help="Command to execute")

    _configure_list_subparser(subparsers)
    _configure_manifest_subparser(subparsers)
    _configure_hist_subparser(subparsers)
    _configure_repair_subparser(subparsers)

    args = parser.parse_args(cli_args)
    if args.version:
        print(f"GPF version: {VERSION} ({RELEASE})")
        sys.exit(0)

    VerbosityConfiguration.set(args)
    command, repo_url = args.command, args.repo_url

    proto = _create_proto(repo_url)

    if command == "manifest":
        _run_manifest_command(proto, **vars(args))
    elif command == "histogram":
        _run_hist_command(proto, **vars(args))
    elif command == "repair":
        _run_repair_command(proto, **vars(args))
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
