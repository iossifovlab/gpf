from __future__ import annotations

import argparse
import os
import sys
import tempfile
from typing import Any, Optional
from dask.distributed import Client, LocalCluster  # type: ignore
from dask_kubernetes import KubeCluster, make_pod_spec  # type: ignore


class DaskClient:
    @staticmethod
    def add_arguments(parser):
        parser.add_argument("-j", "--jobs", type=int, default=None,
                            help="Number of jobs to run in parallel. \
Defaults to the number of processors on the machine")
        parser.add_argument("--kubernetes", default=False,
                            action="store_true",
                            help="Run computation in a kubernetes cluster")
        parser.add_argument("--envvars", nargs="*", default=[],
                            help="Environment variables to pass to "
                            "kubernetes workers")
        parser.add_argument("--container-image",
                            default="registry.seqpipe.org/seqpipe-gpf:"
                            "dask-for-hist-compute_fc69179-14",
                            help="Docker image to use when submitting "
                            "jobs to kubernetes")
        parser.add_argument("--image-pull-secrets", nargs="*",
                            help="Secrets to use when pulling "
                            "the docker image")
        parser.add_argument("--sge", default=False,
                            action="store_true",
                            help="Run computation on a Sun Grid Engine \
cluster. When using this command it is highly advisable to manually specify \
the number of workers using -j")
        parser.add_argument("--dashboard-port", type=int,
                            help="Port on which to run Dask Dashboard")
        parser.add_argument("--log-dir",
                            help="Directory where to store SGE worker logs")

    @classmethod
    def from_arguments(cls, args: argparse.Namespace) -> DaskClient:
        n_jobs = args.jobs or os.cpu_count()

        tmp_dir = tempfile.TemporaryDirectory()

        if args.kubernetes:
            env = cls._get_env_vars(args.envvars)
            extra_pod_config = {}
            if args.image_pull_secrets:
                extra_pod_config["imagePullSecrets"] = [
                    {"name": name} for name in args.image_pull_secrets
                ]
            pod_spec = make_pod_spec(image=args.container_image,
                                     extra_pod_config=extra_pod_config)
            cluster = KubeCluster(pod_spec, env=env)
            cluster.scale(n_jobs)
        elif args.sge:
            try:
                #  pylint: disable=import-outside-toplevel
                from dask_jobqueue import SGECluster  # type: ignore
            except Exception:
                print("No dask-jobqueue found. Please install it using:"
                      " mamba install dask-jobqueue -c conda-forge",
                      file=sys.stderr)
                return None

            dashboard_config: dict[str, Any] = {}
            if args.dashboard_port:
                dashboard_config["scheduler_options"] = \
                    {"dashboard_address": f":{args.dashboard_port}"}
            cluster = SGECluster(n_workers=n_jobs,
                                 queue="all.q",
                                 walltime="1500000",
                                 cores=1,
                                 processes=1,
                                 memory="2GB",
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
        return DaskClient(Client(cluster), cluster, tmp_dir)

    def __init__(self, client, cluster, tmp_dir):
        self.client = client
        self.cluster = cluster
        self._tmp_dir = tmp_dir

    def __enter__(self):
        return self.client

    def __exit__(self, *exc_info):
        self.client.close()
        self.cluster.close()
        self._tmp_dir.cleanup()

    @staticmethod
    def _get_env_vars(var_names):
        res = {}
        for var_name in var_names:
            res[var_name] = os.getenv(var_name)
        return res
