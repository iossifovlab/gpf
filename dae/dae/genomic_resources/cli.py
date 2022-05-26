"""Provides CLI for management of genomic resources repositories."""
import sys
import logging
import pathlib
import argparse
import time
from typing import cast
from urllib.parse import urlparse
from dae.dask.client_factory import DaskClient

from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.url_repository import GenomicResourceURLRepo
from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository, load_definition_file, \
    get_configured_definition
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.score_statistics import HistogramBuilder
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema
from dae.annotation.annotation_factory import AnnotationConfigParser


logger = logging.getLogger(__file__)


class VerbosityConfiguration:
    """Defines common configuration for verbosity of loggers."""

    @staticmethod
    def set_argumnets(parser: argparse.ArgumentParser) -> None:
        """Add verbosity arguments to argument parser."""
        parser.add_argument("--verbose", "-v", "-V", action="count", default=0)

    @staticmethod
    def set(args) -> None:
        """Reads verbosity settings from parsed arguments and sets logger."""
        if args.verbose == 1:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose >= 2:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)


def cli_manage(cli_args=None):
    """Provides CLI for repository management."""
    if not cli_args:
        cli_args = sys.argv[1:]

    desc = "Genomic Resource Repository Management Tool"
    parser = argparse.ArgumentParser(description=desc)
    subparsers = parser.add_subparsers(dest="command",
                                       help="Command to execute")

    parser_index = subparsers.add_parser("index", help="Index a GR Repo")
    parser_index.add_argument("repo_dir", type=str,
                              help="Path to the GR Repo to index")
    parser_index.add_argument("--verbose", "-V", action="count", default=0)

    parser_list = subparsers.add_parser("list", help="List a GR Repo")
    parser_list.add_argument("repo_dir", type=str,
                             help="Path to the GR Repo to list")
    parser_list.add_argument("--verbose", "-V", action="count", default=0)

    parser_hist = subparsers.add_parser("histogram",
                                        help="Build the histograms \
                                        for a resource")
    parser_hist.add_argument("repo_dir", type=str,
                             help="Path to the GR Repo")
    parser_hist.add_argument("resource", type=str,
                             help="Resource to generate histograms for")
    parser_hist.add_argument("--verbose", "-V", action="count", default=0)
    parser_hist.add_argument("--region-size", type=int, default=3_000_000,
                             help="Number of records to process in parallel")
    parser_hist.add_argument("-f", "--force", default=False,
                             action="store_true", help="Ignore histogram "
                             "hashes and always precompute all histograms")
    DaskClient.add_arguments(parser_hist)

    args = parser.parse_args(cli_args)
    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    cmd, repo_dir = args.command, args.repo_dir

    repo = _create_repo(repo_dir)

    if cmd == "index":
        for res in repo.get_all_resources():
            repo.update_manifest(res)

        repo.save_content_file()

    elif cmd == "list":
        for res in repo.get_all_resources():
            res_size = sum([fs for _, fs, _ in res.get_files()])
            print(
                f"{res.get_type():20} {res.get_version_str():7s} "
                f"{len(list(res.get_files())):2d} {res_size:12d} "
                f"{res.get_id()}")

    elif cmd == "histogram":
        res = repo.get_resource(args.resource)
        if res is None:
            logger.error("Cannot find resource %s", args.resource)
            sys.exit(1)
        builder = HistogramBuilder(res)

        dask_client = DaskClient.from_arguments(args)
        if dask_client is None:
            sys.exit(1)

        with dask_client as client:
            histograms = builder.build(client, force=args.force,
                                       only_dirty=True,
                                       region_size=args.region_size)

        hist_out_dir = "histograms"
        logger.info("Saving histograms in %s", hist_out_dir)
        builder.save(histograms, hist_out_dir)
    else:
        logger.error("Unknown command {cmd}. The known commands are index, "
                     "list and histogram")


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


def cli_cache_repo(argv=None):
    """Provides CLI for caching repository."""
    if not argv:
        argv = sys.argv[1:]

    description = "Repository cache tool - caches all resources in a given " \
        "repository"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--definition", default=None, help="Repository definition file"
    )
    parser.add_argument(
        "--jobs", "-j", help="Number of jobs running in parallel",
        default=4, type=int,
    )
    parser.add_argument(
        "--instance", default=None,
        help="gpf_instance.yaml to use for selective cache"
    )
    parser.add_argument(
        "--annotation", default=None,
        help="annotation.yaml to use for selective cache"
    )
    VerbosityConfiguration.set_argumnets(parser)

    args = parser.parse_args(argv)
    VerbosityConfiguration.set(args)

    start = time.time()
    if args.definition is not None:
        definition = load_definition_file(args.definition)
    else:
        definition = get_configured_definition()

    repository = build_genomic_resource_repository(definition=definition)
    if not isinstance(repository, GenomicResourceCachedRepo):
        raise ValueError(
            "This tool works only if the top configured "
            "repository is cached.")
    repository = cast(GenomicResourceCachedRepo, repository)

    resources = set()
    annotation = None

    if args.instance is not None and args.annotation is not None:
        raise ValueError(
            "This tool cannot handle both annotation and instance flags"
        )

    if args.instance is not None:
        config = GPFConfigParser.load_config(args.instance, dae_conf_schema)
        resources.add(config.reference_genome.resource_id)
        resources.add(config.gene_models.resource_id)
        if config.annotation is not None:
            annotation = config.annotation.conf_file
    elif args.annotation is not None:
        annotation = args.annotation

    if annotation is not None:
        config = AnnotationConfigParser.parse_config_file(annotation)
        resources.update(_extract_resource_ids_from_annotation_conf(config))

    if len(resources) > 0:
        resources = list(resources)
    else:
        resources = None

    repository.cache_resources(workers=args.jobs, resource_ids=resources)

    elapsed = time.time() - start

    logger.info("Cached all resources in %.2f secs", elapsed)


def _create_repo(dr):
    repo_url = urlparse(dr)
    if not repo_url.scheme or repo_url.scheme == "file":
        dr = pathlib.Path(dr)
        repo = GenomicResourceDirRepo("", dr)
    else:
        repo = GenomicResourceURLRepo("", dr)
    return repo
