"""Factory for creatio of dask client objects from config or CLI arguments."""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from typing import Optional, Dict, Any

from dask.distributed import Client, LocalCluster  # type: ignore
from dask_kubernetes import make_pod_spec  # type: ignore
from dask_kubernetes.classic import KubeCluster  # type: ignore


class DaskClient:
    """Factory for Dask client objects."""

    @staticmethod
    def add_arguments(parser):
        """Configure argparser with Dask client parameters."""
        group = parser.add_argument_group(title="Dask cluster")
        group.add_argument(
            "-j", "--jobs", type=int, default=None,
            help="Number of jobs to run in parallel. Defaults to the number "
            "of processors on the machine")
        group.add_argument(
            "--kubernetes", default=False,
            action="store_true",
            help="Run computation in a kubernetes cluster")
        group.add_argument(
            "--envvars", nargs="*", default=[],
            help="Environment variables to pass to "
            "kubernetes workers")
        group.add_argument(
            "--container-image",
            default="registry.seqpipe.org/iossifovlab-gpf:"
            "master",
            help="Docker image to use when submitting "
            "jobs to kubernetes")
        group.add_argument(
            "--image-pull-secrets", nargs="*",
            help="Secrets to use when pulling "
            "the docker image")
        group.add_argument(
            "--sge", default=False,
            action="store_true",
            help="Run computation on a Sun Grid Engine cluster. When using "
            "this command it is highly advisable to manually specify "
            "the number of workers using -j")
        group.add_argument(
            "--dashboard-port", type=int,
            help="Port on which to run Dask Dashboard")
        group.add_argument(
            "--log-dir",
            help="Directory where to store SGE worker logs")

    @classmethod
    def from_arguments(cls, args: argparse.Namespace) -> Optional[DaskClient]:
        return DaskClient.from_dict(vars(args))

    @classmethod
    def from_dict(cls, kwargs) -> Optional[DaskClient]:
        """Configure a DaskClient from a configuration dict."""
        n_jobs = kwargs.get("jobs")
        if not n_jobs:
            n_jobs = os.cpu_count()

        dashboard_config: Dict[str, Any] = {}
        if kwargs.get("dashboard_port"):
            dashboard_config["scheduler_options"] = {
                "dashboard_address":
                f":{kwargs.get('dashboard_port', 8787)}"
            }
        if kwargs.get("log_dir"):
            log_dir = kwargs.get("log_dir")
        else:
            # pylint: disable=consider-using-with
            tmp_dir = tempfile.TemporaryDirectory()
            log_dir = tmp_dir.name

        if kwargs.get("kubernetes"):
            env = cls._get_env_vars(kwargs.get("envvars"))
            extra_pod_config = {}
            if kwargs.get("image_pull_secrets"):
                extra_pod_config["imagePullSecrets"] = [
                    {"name": name}
                    for name in kwargs.get(
                        "image_pull_secrets", [])
                ]
            pod_spec = make_pod_spec(
                image=kwargs.get("container_image"),
                extra_pod_config=extra_pod_config)
            cluster = KubeCluster(pod_spec, env=env)
            cluster.scale(n_jobs)
        elif kwargs.get("sge"):
            try:
                #  pylint: disable=import-outside-toplevel
                from dask_jobqueue import SGECluster  # type: ignore
            except ModuleNotFoundError:
                print("No dask-jobqueue found. Please install it using:"
                      " mamba install dask-jobqueue -c conda-forge",
                      file=sys.stderr)
                return None

            cluster = SGECluster(n_workers=n_jobs,
                                 queue="all.q",
                                 walltime="1500000",
                                 cores=1,
                                 processes=1,
                                 memory="2GB",
                                 log_directory=log_dir,
                                 local_directory=tmp_dir.name,
                                 **dashboard_config)
        else:
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
