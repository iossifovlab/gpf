from typing import Any, Dict, Optional, Tuple
from distributed.client import Client
import dask

_CLUSTER_TYPES = {}


def set_up_local_cluster(cluster_conf, number_of_threads):
    from distributed.deploy.local import LocalCluster
    cluster = LocalCluster(**cluster_conf)
    if number_of_threads is not None:
        cluster.scale(cores=number_of_threads)
    return cluster

def set_up_sge_cluster(cluster_conf, number_of_threads):
    from dask_jobqueue import SGECluster

    cluster = SGECluster(**cluster_conf)
    if number_of_threads is not None:
        cluster.scale(cores=number_of_threads)
    return cluster


_CLUSTER_TYPES["local"] = set_up_local_cluster
_CLUSTER_TYPES["sge"] = set_up_sge_cluster



def setup_client_from_config(cluster_config,
                 number_of_threads: Optional[int] = None) \
        -> Tuple[Client, Dict[str, Any]]:

    cluster_type = cluster_config["type"]

    cluster = _CLUSTER_TYPES[cluster_type](
        cluster_config["params"], number_of_threads)
    client = Client(cluster)
    return client, cluster_config

def setup_client(cluster_name: Optional[str] = None,
                 number_of_threads: Optional[int] = None) \
        -> Tuple[Client, Dict[str, Any]]:

    if cluster_name is None:
        cluster_name = dask.config.get("dae_named_cluster.default")

    clusters = {conf["name"]: conf
                for conf in dask.config.get("dae_named_cluster.clusters")}

    cluster_config = clusters[cluster_name]
    return setup_client_from_config(cluster_config, number_of_threads)
