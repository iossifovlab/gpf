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

def set_up_slurm_cluster(cluster_conf, number_of_threads):
    from dask_jobqueue import SLURMCluster

    cluster = SLURMCluster(**cluster_conf)
    if number_of_threads is not None:
        cluster.scale(cores=number_of_threads)
    return cluster

def set_up_kubernetes_cluster(cluster_conf, number_of_threads):
    from dask_kubernetes import KubeCluster, make_pod_spec
    import os

    env = {}
    if 'envvars' in cluster_conf:
        env = {v:os.environ[v] for v in cluster_conf['envvars']}
    
    pod_spec = make_pod_spec(
                image=cluster_conf["container_image"],
                extra_pod_config=cluster_conf.get("extra_pod_config",{}))
    cluster = KubeCluster(pod_spec, env=env)
    if number_of_threads is not None:
        cluster.scale(cores=number_of_threads)
    return cluster


_CLUSTER_TYPES["local"] = set_up_local_cluster
_CLUSTER_TYPES["sge"] = set_up_sge_cluster
_CLUSTER_TYPES["slurm"] = set_up_slurm_cluster
_CLUSTER_TYPES["kubernetes"] = set_up_kubernetes_cluster



def setup_client_from_config(cluster_config,
                 number_of_threads: Optional[int] = None) \
        -> Tuple[Client, Dict[str, Any]]:

    print("CLUSTER CONFIG:", cluster_config)
    cluster_type = cluster_config["type"]

    cluster_params = cluster_config.get("params",{})
    cluster = _CLUSTER_TYPES[cluster_type](cluster_params, number_of_threads)
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
