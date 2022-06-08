"""Provides CLI for management of genomic resources repositories."""
import os
import sys
import logging
import argparse
from dae.dask.client_factory import DaskClient

from dae.__version__ import VERSION, RELEASE
from dae.genomic_resources.fsspec_protocol import build_fsspec_protocol
from dae.genomic_resources.histogram import HistogramBuilder
# from dae.genomic_resources.repository_helpers import RepositoryWorkflowHelper


logger = logging.getLogger(__file__)


class VerbosityConfiguration:
    """Defines common configuration for verbosity of loggers."""

    @staticmethod
    def set_argumnets(parser: argparse.ArgumentParser) -> None:
        """Add verbosity arguments to argument parser."""
        parser.add_argument("--verbose", "-v", "-V", action="count", default=0)

    @staticmethod
    def set(args) -> None:
        """Read verbosity settings from parsed arguments and sets logger."""
        if args.verbose == 1:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose >= 2:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)


def _configure_hist_subparser(subparsers):
    parser_hist = subparsers.add_parser("histogram",
                                        help="Build the histograms \
                                        for a resource")
    parser_hist.add_argument("repo_dir", type=str,
                             help="Path to the GR Repo")
    parser_hist.add_argument("resource", type=str,
                             help="Resource to generate histograms for")

    VerbosityConfiguration.set_argumnets(parser_hist)
    parser_hist.add_argument("--region-size", type=int, default=3000000,
                             help="Number of records to process in parallel")
    parser_hist.add_argument("-f", "--force", default=False,
                             action="store_true", help="Ignore histogram "
                             "hashes and always precompute all histograms")
    DaskClient.add_arguments(parser_hist)


def _run_hist_command(repo, args):
    res = repo.get_resource(args.resource)
    if res is None:
        logger.error("Cannot find resource %s", args.resource)
        sys.exit(1)
    builder = HistogramBuilder(res)

    dask_client = DaskClient.from_arguments(args)
    if dask_client is None:
        sys.exit(1)

    with dask_client as client:
        histograms = builder.build(
            client, force=args.force,
            only_dirty=True,
            region_size=args.region_size)

    hist_out_dir = "histograms"
    logger.info("Saving histograms in %s", hist_out_dir)
    builder.save(histograms, hist_out_dir)


def _configure_list_subparser(subparsers):
    parser_list = subparsers.add_parser("list", help="List a GR Repo")
    parser_list.add_argument("repo_dir", type=str,
                             help="Path to the GR Repo to list")
    VerbosityConfiguration.set_argumnets(parser_list)


def _run_list_command(proto, _args):
    for res in proto.get_all_resources():
        res_size = sum([fs for _, fs, _ in res.get_manifest().get_files()])
        print(
            f"{res.get_type():20} {res.get_version_str():7s} "
            f"{len(list(res.get_manifest().get_files())):2d} {res_size:12d} "
            f"{res.get_id()}")


def _configure_index_subparser(subparsers):
    parser_index = subparsers.add_parser("index", help="Index a GR Repo")
    parser_index.add_argument(
        "repo_dir", type=str,
        help="Path to the GR Repo to index")
    VerbosityConfiguration.set_argumnets(parser_index)
    parser_index.add_argument(
        "-r", "--resource", type=str, default=None,
        help="specifies a single resource ID to be indexed")
    parser_index.add_argument(
        "-n", "--dry-run", default=False, action="store_true",
        help="only checks if the manifest update is needed and reports")


def _get_resources_list(proto, **kwargs):
    res_id = kwargs.get("resource")
    if res_id is not None:
        res = proto.get_resource(res_id)
        if res is None:
            logger.error(
                "resource %s not found in repository %s",
                res_id, proto.url)
            sys.exit(1)
        resources = [res]
    else:
        resources = proto.get_all_resources()
    return resources


def _run_index_command(proto, **kwargs):
    resources = _get_resources_list(proto, **kwargs)
    # dry_run = kwargs.get("dry_run", False)

    for res in resources:
        proto.update_manifest(res)
    proto.build_content_file()


def _configure_checkout_subparser(subparsers):
    parser_index = subparsers.add_parser(
        "checkout", help="checkout Manifest timestamps.")
    parser_index.add_argument(
        "repo_dir", type=str,
        help="path to the genomic resources repository directory")
    VerbosityConfiguration.set_argumnets(parser_index)
    parser_index.add_argument(
        "-r", "--resource", type=str, default=None,
        help="specifies a single resource ID to process")
    parser_index.add_argument(
        "-n", "--dry-run", default=False, action="store_true",
        help="only checks if the manifest update is needed and reports")


def _run_checkout_command(repo, **kwargs):
    # resources = _get_resources_list(repo, **kwargs)
    # dry_run = kwargs.get("dry_run", False)

    # repo_helper = RepositoryWorkflowHelper(repo)
    # for res in resources:
    #     repo_helper.checkout_manifest_timestamps(res, dry_run)
    # repo_helper.check_repository_content_file()
    pass


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

    _configure_index_subparser(subparsers)
    _configure_list_subparser(subparsers)
    _configure_hist_subparser(subparsers)
    _configure_checkout_subparser(subparsers)

    args = parser.parse_args(cli_args)
    if args.version:
        print(f"GPF version: {VERSION} ({RELEASE})")
        sys.exit(0)

    VerbosityConfiguration.set(args)
    command, repo_dir = args.command, args.repo_dir

    proto = _create_proto(repo_dir)

    if command == "index":
        _run_index_command(proto, **vars(args))
    elif command == "list":
        _run_list_command(proto, args)
    elif command == "histogram":
        _run_hist_command(proto, args)
    elif command == "checkout":
        _run_checkout_command(proto, **vars(args))
    else:
        logger.error(
            "Unknown command %s. The known commands are index, "
            "list and histogram", command)
        sys.exit(1)


def _extract_resource_ids_from_annotation_conf(config):
    resources = set()
    for annotator in config:
        print(annotator)
        for key, val in annotator.items():
            if key in [
                "resource_id",
                "target_genome",
                "chain",
                "genome"
            ]:
                resources.add(val)
    return resources


def _create_proto(repo_url):
    if not os.path.isabs(repo_url):
        repo_url = os.path.abspath(repo_url)

    proto = build_fsspec_protocol(proto_id="manage", root_url=repo_url)
    return proto


# def cli_cache_repo(argv=None):
#     """Provides CLI for caching repository."""
#     if not argv:
#         argv = sys.argv[1:]

#     description = "Repository cache tool - caches all resources
#           in a given " \
#         "repository"
#     parser = argparse.ArgumentParser(description=description)
#     parser.add_argument(
#         "--definition", default=None, help="Repository definition file"
#     )
#     parser.add_argument(
#         "--jobs", "-j", help="Number of jobs running in parallel",
#         default=4, type=int,
#     )
#     parser.add_argument(
#         "--instance", default=None,
#         help="gpf_instance.yaml to use for selective cache"
#     )
#     parser.add_argument(
#         "--annotation", default=None,
#         help="annotation.yaml to use for selective cache"
#     )
#     VerbosityConfiguration.set_argumnets(parser)

#     args = parser.parse_args(argv)
#     VerbosityConfiguration.set(args)

#     start = time.time()
#     if args.definition is not None:
#         definition = load_definition_file(args.definition)
#     else:
#         definition = get_configured_definition()

#     repository = build_genomic_resource_repository(definition=definition)
#     if not isinstance(repository, GenomicResourceCachedRepo):
#         raise ValueError(
#             "This tool works only if the top configured "
#             "repository is cached.")
#     repository = cast(GenomicResourceCachedRepo, repository)

#     resources = set()
#     annotation = None

#     if args.instance is not None and args.annotation is not None:
#         raise ValueError(
#             "This tool cannot handle both annotation and instance flags"
#         )

#     if args.instance is not None:
#         config = GPFConfigParser.load_config(args.instance, dae_conf_schema)
#         resources.add(config.reference_genome.resource_id)
#         resources.add(config.gene_models.resource_id)
#         if config.annotation is not None:
#             annotation = config.annotation.conf_file
#     elif args.annotation is not None:
#         annotation = args.annotation

#     if annotation is not None:
#         config = AnnotationConfigParser.parse_config_file(annotation)
#         resources.update(_extract_resource_ids_from_annotation_conf(config))

#     if len(resources) > 0:
#         resources = list(resources)
#     else:
#         resources = None

#     repository.cache_resources(workers=args.jobs, resource_ids=resources)

#     elapsed = time.time() - start

#     logger.info("Cached all resources in %.2f secs", elapsed)
