import os
import sys
import logging
import pathlib
import argparse
import time
from typing import cast
from urllib.parse import urlparse
import tempfile

from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.url_repository import GenomicResourceURLRepo
from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository, load_definition_file, \
    get_configured_definition
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources.score_statistics import HistogramBuilder

from dask.distributed import Client, LocalCluster
from dask_kubernetes import KubeCluster, make_pod_spec

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
    parser_index.add_argument('--verbose', '-V', action='count', default=0)

    parser_list = subparsers.add_parser('list', help='List a GR Repo')
    parser_list.add_argument('repo_dir', type=str,
                             help='Path to the GR Repo to list')
    parser_list.add_argument('--verbose', '-V', action='count', default=0)

    parser_hist = subparsers.add_parser('histogram',
                                        help='Build the histograms \
                                        for a resource')
    parser_hist.add_argument('repo_dir', type=str,
                             help='Path to the GR Repo')
    parser_hist.add_argument('resource', type=str,
                             help='Resource to generate histograms for')
    parser_hist.add_argument('--verbose', '-V', action='count', default=0)
    parser_hist.add_argument('-j', '--jobs', type=int, default=None,
                             help='Number of jobs to run in parallel. \
 Defaults to the number of processors on the machine')
    parser_hist.add_argument("--region-size", type=int, default=3000000,
                             help="Number of records to process in parallel")
    parser_hist.add_argument('--kubernetes', default=False,
                             action='store_true',
                             help='Run computation in a kubernetes cluster')
    parser_hist.add_argument('--envvars', nargs='*', default=[],
                             help='Environment variables to pass to '
                             'kubernetes workers')
    parser_hist.add_argument('--container-image',
                             default='registry.seqpipe.org/seqpipe-gpf:'
                             'dask-for-hist-compute_fc69179-14',
                             help='Docker image to use when submitting '
                             'jobs to kubernetes')
    parser_hist.add_argument('--image-pull-secrets', nargs='*',
                             help='Secrets to use when pulling '
                             'the docker image')
    parser_hist.add_argument('-f', '--force', default=False,
                             action='store_true', help='Ignore histogram '
                             'hashes and always precompute all histograms')
    parser_hist.add_argument("--sge", default=False,
                             action="store_true",
                             help="Run computation on a Sun Grid Engine \
cluster. When using this command it is highly advisable to manually specify \
the number of workers using -j")
    parser_hist.add_argument("--dashboard-port", type=int,
                             help="Port on which to run Dask Dashboard")
    parser_hist.add_argument("--log-dir",
                             help="Directory where to store SGE worker logs")

    args = parser.parse_args(cli_args)
    if args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    cmd, dr = args.command, args.repo_dir

    GRR = _create_repo(dr)

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
            logger.error(f"Cannot find resource {args.resource}")
            sys.exit(1)
        builder = HistogramBuilder(gr)
        n_jobs = args.jobs or os.cpu_count()

        tmp_dir = tempfile.TemporaryDirectory()

        if args.kubernetes:
            env = _get_env_vars(args.envvars)
            extra_pod_config = {}
            if args.image_pull_secrets:
                extra_pod_config['imagePullSecrets'] = [
                    {'name': name} for name in args.image_pull_secrets
                ]
            pod_spec = make_pod_spec(image=args.container_image,
                                     extra_pod_config=extra_pod_config)
            cluster = KubeCluster(pod_spec, env=env)
            cluster.scale(n_jobs)
        elif args.sge:
            try:
                from dask_jobqueue import SGECluster
            except Exception:
                logger.error("No dask-jobqueue found. Please install it using:"
                             " mamba install dask-jobqueue -c conda-forge")
                sys.exit(1)

            dashboard_config = {}
            if args.dashboard_port:
                dashboard_config["scheduler_options"] = \
                    {"dashboard_address": f":{args.dashboard_port}"}
            cluster = SGECluster(n_workers=n_jobs,
                                 queue="all.q",
                                 walltime="1500000",
                                 cores=1,
                                 processes=1,
                                 memory='2GB',
                                 log_directory=args.log_dir or tmp_dir.name,
                                 local_directory=tmp_dir.name,
                                 **dashboard_config)
        else:
            dashboard_config = {}
            if args.dashboard_port:
                dashboard_config["dashboard_address"] = \
                    f":{args.dashboard_port}"
            cluster = LocalCluster(n_workers=n_jobs, threads_per_worker=1,
                                   local_directory=tmp_dir.name,
                                   **dashboard_config)
        with tmp_dir, cluster:
            with Client(cluster) as client:
                histograms = builder.build(client, force=args.force,
                                           only_dirty=True,
                                           region_size=args.region_size)

        hist_out_dir = "histograms"
        logger.info(f"Saving histograms in {hist_out_dir}")
        builder.save(histograms, hist_out_dir)
    else:
        logger.error(f'Unknown command {cmd}. The known commands are index, '
                     'list and histogram')


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


def _create_repo(dr):
    repo_url = urlparse(dr)
    if not repo_url.scheme or repo_url.scheme == 'file':
        dr = pathlib.Path(dr)
        GRR = GenomicResourceDirRepo("", dr)
    else:
        GRR = GenomicResourceURLRepo("", dr)
    return GRR


def _get_env_vars(var_names):
    res = {}
    for var_name in var_names:
        res[var_name] = os.getenv(var_name)
    return res


if __name__ == '__main__':
    cli_browse(sys.argv[1:])
