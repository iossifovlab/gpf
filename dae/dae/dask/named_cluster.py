import os
from typing import Any, Dict, Optional, Tuple
from distributed.client import Client
import dask

_CLUSTER_TYPES = {}


def set_up_local_cluster(cluster_conf):
    # pylint: disable=import-outside-toplevel
    from dask.distributed import LocalCluster
    cluster = LocalCluster(**cluster_conf)
    return cluster


def set_up_sge_cluster(cluster_conf):
    # pylint: disable=import-outside-toplevel
    from dask_jobqueue import SGECluster
    return SGECluster(**cluster_conf)


def set_up_slurm_cluster(cluster_conf):
    # pylint: disable=import-outside-toplevel
    from dask_jobqueue import SLURMCluster
    return SLURMCluster(**cluster_conf)


def set_up_kubernetes_cluster(cluster_conf):
    """Create a kubernetes cluster."""
    # pylint: disable=import-outside-toplevel
    from dask_kubernetes.operator.kubecluster import \
        KubeCluster, \
        make_cluster_spec

    env = {}
    if "envvars" in cluster_conf:
        env = {v: os.environ[v] for v in cluster_conf["envvars"]}

    spec = make_cluster_spec(
        name="gpf-dask-cluster",
        image=cluster_conf["container_image"],
        env=env,
    )

    if cluster_conf.get("image_pull_secrets"):
        secrets = [
            {"name": name}
            for name in cluster_conf.get("image_pull_secrets", [])
        ]
        spec["spec"]["worker"]["spec"]["imagePullSecrets"] = secrets
        spec["spec"]["scheduler"]["spec"]["imagePullSecrets"] = secrets

    cluster = KubeCluster(n_workers=1, custom_cluster_spec=spec)
    return cluster


_CLUSTER_TYPES["local"] = set_up_local_cluster
_CLUSTER_TYPES["sge"] = set_up_sge_cluster
_CLUSTER_TYPES["slurm"] = set_up_slurm_cluster
_CLUSTER_TYPES["kubernetes"] = set_up_kubernetes_cluster


def setup_client_from_config(cluster_config,
                             number_of_threads_param: Optional[int] = None) \
        -> Tuple[Client, Dict[str, Any]]:
    """Create a dask client from the provided config."""
    print("CLUSTER CONFIG:", cluster_config)
    cluster_type = cluster_config["type"]

    cluster_params = cluster_config.get("params", {})
    cluster = _CLUSTER_TYPES[cluster_type](cluster_params)

    number_of_threads = cluster_config.get("number_of_threads", None)
    if number_of_threads_param is not None:
        number_of_threads = number_of_threads_param
    if number_of_threads is not None:
        cluster.scale(n=number_of_threads)
    elif "adapt_params" in cluster_config:
        cluster.adapt(**cluster_config["adapt_params"])

    client = Client(cluster)
    return client, cluster_config


def setup_client(cluster_name: Optional[str] = None,
                 number_of_threads: Optional[int] = None) \
        -> Tuple[Client, Dict[str, Any]]:
    """Create a dask client from the provided cluster name."""
    if cluster_name is None:
        cluster_name = dask.config.get("dae_named_cluster.default")

    clusters = {conf["name"]: conf
                for conf in dask.config.get("dae_named_cluster.clusters")}

    cluster_config = clusters[cluster_name]
    return setup_client_from_config(cluster_config, number_of_threads)
