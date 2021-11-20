import sys
import logging
import pathlib
import argparse
import time

from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository, load_definition_file, \
    get_configured_definition

logger = logging.getLogger(__file__)


def cli_browse(args=None):
    if not args:
        args = sys.argv[1:]

    grr = build_genomic_resource_repository()
    for gr in grr.get_all_resources():
        print("%20s %20s %-7s %2d %10d %s" %
              (gr.repo.repo_id, gr.get_resource_type(), gr.get_version_str(),
               len(list(gr.get_files())),
                  sum([fs for _, fs, _ in gr.get_files()]), gr.get_id()))


def cli_manage(args=None):
    if not args:
        args = sys.argv[1:]

    if len(args) != 2:
        print("Need two arguments: <command> and <repository directory>")
        return

    cmd, dr = args

    dr = pathlib.Path(dr)
    GRR = GenomicResourceDirRepo("", dr)

    if cmd == "index":
        for gr in GRR.get_all_resources():
            gr.update_stats()
            gr.update_manifest()

        if not (dr / GR_CONF_FILE_NAME).is_file():
            GRR.save_content_file()
    elif cmd == "list":
        for gr in GRR.get_all_resources():

            print("%20s %-7s %2d %10d %s" %
                  (gr.get_resource_type(), gr.get_version_str(),
                   len(list(gr.get_files())),
                      sum([fs for _, fs, _ in gr.get_files()]), gr.get_id()))
    else:
        print(f'Unknown command {cmd}. The known commands are index and list')


def cli_cache_repo(args=None):
    if not args:
        args = sys.argv[1:]

    description = \
        "Repository cache tool - caches all resources in a given repository"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--verbose', '-V', '-v', action='count', default=0)
    parser.add_argument(
        "--definition", default=None, help="Repository definition file"
    )

    args = parser.parse_args(args)
    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    start = time.time()
    if args.definition is not None:
        definition = load_definition_file(args.definition)
    else:
        definition = get_configured_definition()

    assert "cache_dir" in definition, \
        "No cache directory specified in definition"

    repository = build_genomic_resource_repository(definition=definition)

    repository.cache_all_resources()

    elapsed = time.time() - start

    logger.info(f"Cached all resources in {elapsed:.2f} secs")


if __name__ == '__main__':
    cli_browse(sys.argv[1:])
