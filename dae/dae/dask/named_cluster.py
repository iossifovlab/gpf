from typing import Optional, Tuple
from distributed.client import Client
import dask

_CLUSTER_TYPES = {}


def set_up_local_cluster(cluster_conf, number_of_threads):
    from distributed.deploy.local import LocalCluster
    cluster = LocalCluster(**cluster_conf)
    if number_of_threads is not None:
        cluster.scale(cores=number_of_threads)
    return cluster


_CLUSTER_TYPES["local"] = set_up_local_cluster


def setup_client(cluster_name: Optional[str] = None,
                 number_of_threads: Optional[int] = None) \
        -> Tuple[Client, str, str]:

    if cluster_name is None:
        cluster_name = dask.config.get("dae_named_cluster.default")

    cluster_config = dict(dask.config.get(
        f"dae_named_cluster.clusters.{cluster_name}"))
    cluster_type = cluster_config["type"]
    del cluster_config['type']

    cluster = _CLUSTER_TYPES[cluster_type](
        cluster_config, number_of_threads)
    client = Client(cluster)
    return client, cluster_name, cluster_type
