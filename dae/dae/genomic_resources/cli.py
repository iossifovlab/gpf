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


def cli_manage(args=None):
    if not args:
        args = sys.argv[1:]

    if len(args) != 2:
        print("Need two arguments: <command> and <repository directory>. "
              "The supported commands are index and list.")
        return

    cmd, dr = args

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
