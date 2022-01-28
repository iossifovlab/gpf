import os
import sys
import logging
import pathlib
import argparse
import time
from typing import cast

from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository, load_definition_file, \
    get_configured_definition
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.score_statistics import HistogramBuilder

logger = logging.getLogger(__file__)


class VerbosityConfiguration:
    @staticmethod
    def set_argumnets(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--verbose', '-v', '-V', action='count', default=0)

    @staticmethod
    def set(args):
        if args.verbose == 1:
            logging.basicConfig(level=logging.INFO)
        elif args.verbose >= 2:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)


def cli_browse(args=None):
    if not args:
        args = sys.argv[1:]

    grr = build_genomic_resource_repository()
    for gr in grr.get_all_resources():
        print("%20s %20s %-7s %2d %12d %s" %
              (gr.repo.repo_id, gr.get_resource_type(), gr.get_version_str(),
               len(list(gr.get_files())),
                  sum([fs for _, fs, _ in gr.get_files()]), gr.get_id()))


def cli_manage(cli_args=None):
    if not cli_args:
        cli_args = sys.argv[1:]

    desc = "Genomic Resource Repository Management Tool"
    parser = argparse.ArgumentParser(description=desc)
    subparsers = parser.add_subparsers(dest='command',
                                       help='Command to execute')

    parser_index = subparsers.add_parser('index', help='Index a GR Repo')
    parser_index.add_argument('repo_dir', type=str,
                              help='Path to the GR Repo to index')

    parser_list = subparsers.add_parser('list', help='List a GR Repo')
    parser_list.add_argument('repo_dir', type=str,
                             help='Path to the GR Repo to list')

    parser_hist = subparsers.add_parser('histogram',
                                        help='Build the histograms \
                                        for a resource')
    parser_hist.add_argument('repo_dir', type=str,
                             help='Path to the GR Repo')
    parser_hist.add_argument('resource', type=str,
                             help='Resource to generate histograms for')

    args = parser.parse_args(cli_args)

    cmd, dr = args.command, args.repo_dir

    dr = pathlib.Path(dr)
    GRR = GenomicResourceDirRepo("", dr)

    if cmd == "index":
        for gr in GRR.get_all_resources():
            gr.update_stats()
            gr.update_manifest()

        GRR.save_content_file()

    elif cmd == "list":
        for gr in GRR.get_all_resources():

            print("%20s %-7s %2d %12d %s" %
                  (gr.get_resource_type(), gr.get_version_str(),
                   len(list(gr.get_files())),
                      sum([fs for _, fs, _ in gr.get_files()]), gr.get_id()))
    elif cmd == "histogram":
        gr = GRR.get_resource(args.resource)
        if gr is None:
            print(f"Cannot find resource {args.resource}")
            sys.exit(1)
        builder = HistogramBuilder()
        histograms = builder.build(gr)
        resource_path = pathlib.Path(args.resource)
        hist_out_dir = dr / resource_path / 'histograms'
        print(f"Saving histograms in {hist_out_dir}")
        builder.save(histograms, hist_out_dir)
    else:
        print(f'Unknown command {cmd}. The known commands are index and list')


def cli_cache_repo(args=None):
    if not args:
        args = sys.argv[1:]

    description = "Repository cache tool - caches all resources in a given "
    "repository"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--definition", default=None, help="Repository definition file"
    )
    VerbosityConfiguration.set_argumnets(parser)

    args = parser.parse_args(args)
    VerbosityConfiguration.set(args)

    start = time.time()
    if args.definition is not None:
        definition = load_definition_file(args.definition)
    else:
        definition = get_configured_definition()

    repository = build_genomic_resource_repository(definition=definition)
    if not isinstance(repository, GenomicResourceCachedRepo):
        raise Exception("This tool works only if the top configured "
                        "repository is cached.")
    repository = cast(GenomicResourceCachedRepo, repository)
    repository.cache_all_resources()

    elapsed = time.time() - start

    logger.info(f"Cached all resources in {elapsed:.2f} secs")


if __name__ == '__main__':
    cli_browse(sys.argv[1:])
