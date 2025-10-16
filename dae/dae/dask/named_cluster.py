import copy
import logging
import os
from collections.abc import Callable
from typing import Any, cast

import dask
import dask.config
from distributed.client import Client
from distributed.deploy import Cluster  # pyright: ignore

_CLUSTER_TYPES: dict[str, Callable[[dict[str, Any]], Cluster]] = {}
logger = logging.getLogger(__name__)


def set_up_local_cluster(cluster_conf: dict[str, Any]) -> Cluster:
    """Create a local cluster using the passed cluster configuration."""
    # pylint: disable=import-outside-toplevel
    from dask.distributed import LocalCluster

    kwargs = copy.copy(cluster_conf)
    number_of_workers = kwargs.pop("number_of_workers", None)
    threads_per_worker = kwargs.pop("threads_per_worker", None)
    if threads_per_worker is not None:
        logger.warning(
            "The 'threads_per_worker' key in the dae_named_cluster config is "
            "not supported. We support only one thread per worker.")
    threads_per_worker = 1

    if number_of_workers is not None:
        kwargs["n_workers"] = number_of_workers
    if threads_per_worker is not None:
        kwargs["threads_per_worker"] = threads_per_worker
    dask.config.set(scheduler="threads")
    return LocalCluster(**kwargs)


def set_up_sge_cluster(cluster_conf: dict[str, Any]) -> Cluster:
    # pylint: disable=import-outside-toplevel
    from dask_jobqueue import SGECluster  # pyright: ignore
    cluster_conf.pop("number_of_workers", None)
    return SGECluster(**cluster_conf)


def set_up_slurm_cluster(cluster_conf: dict[str, Any]) -> Cluster:
    # pylint: disable=import-outside-toplevel
    from dask_jobqueue import SLURMCluster  # pyright: ignore
    cluster_conf.pop("number_of_workers", None)
    return SLURMCluster(**cluster_conf)


def set_up_kubernetes_cluster(cluster_conf: dict[str, Any]) -> Cluster:
    """Create a kubernetes cluster."""
    # pylint: disable=import-outside-toplevel
    from dask_kubernetes.operator.kubecluster import (
        KubeCluster,
        make_cluster_spec,
    )

    cluster_conf.pop("number_of_workers", None)
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

    return cast(Cluster, KubeCluster(n_workers=1, custom_cluster_spec=spec))


_CLUSTER_TYPES["local"] = set_up_local_cluster
_CLUSTER_TYPES["sge"] = set_up_sge_cluster
_CLUSTER_TYPES["slurm"] = set_up_slurm_cluster
_CLUSTER_TYPES["kubernetes"] = set_up_kubernetes_cluster


def set_up_manual_client(cluster_conf: dict[str, Any]) -> Client:
    """Create a dask client using the passed cluster configuration."""
    # pylint: disable=import-outside-toplevel
    params = cluster_conf.get("params", {})
    scheduler_address = params.pop("address", None)

    if scheduler_address is None:
        raise ValueError(
            "Cluster configuration must contain scheduler 'address' key.")

    return Client(address=scheduler_address, **params)


def setup_client_from_config(
    cluster_config: dict[str, Any], *,
    number_of_workers: int | None = None,
) -> tuple[Client, dict[str, Any]]:
    """Create a dask client from the provided config."""
    logger.info("CLUSTER CONFIG: %s", cluster_config)
    _adjust_default_distributed_config()
    cluster_type = cluster_config["type"]
    if cluster_type == "manual":
        return set_up_manual_client(cluster_config), cluster_config

    cluster_params = cluster_config.get("params", {})
    cluster_params["number_of_workers"] = number_of_workers

    threads_per_worker = cluster_params.get("threads_per_worker")
    if threads_per_worker is not None and threads_per_worker != 1:
        logger.warning(
            "The 'threads_per_worker' key in the named cluster config is "
            "not supported. We support only one thread per worker.")
        cluster_params["threads_per_worker"] = 1

    cluster = _CLUSTER_TYPES[cluster_type](cluster_params)

    number_of_threads_config = cluster_config.get("number_of_threads")
    if number_of_threads_config is not None:
        logger.warning(
            "The 'number_of_threads' key in the named cluster config is "
            "deprecated. Use 'number_of_workers' instead.")

    number_of_workers_config = cluster_config.get(
        "number_of_workers", number_of_threads_config)

    if number_of_workers is not None:
        logger.info(
            "Overriding the configurated number of workers from "
            "CLI parameter to %d workers.",
            number_of_workers,
        )
        number_of_workers_config = number_of_workers

    if number_of_workers_config is not None:
        cluster.scale(n=number_of_workers_config)
    elif "adapt_params" in cluster_config:
        cluster.adapt(**cluster_config["adapt_params"])

    client = Client(cluster)
    return client, cluster_config


def _adjust_default_distributed_config() -> None:
    """Adjust some default distributed config values if they are not set."""
    task_duration = dask.config.get(
        "dae_named_cluster.distributed.scheduler.unknown-task-duration")
    dask.config.config[
        "distributed"]["scheduler"]["unknown-task-duration"] = task_duration

    memory_pause = dask.config.get(
        "dae_named_cluster.distributed.worker.memory.pause")
    dask.config.config[
        "distributed"]["worker"]["memory"]["pause"] = memory_pause


def setup_client(
    cluster_name: str | None = None,
    number_of_workers: int | None = None,
) -> tuple[Client, dict[str, Any]]:
    """Create a dask client from the provided cluster name."""
    if cluster_name is None:
        cluster_name = dask.config.get(  # pyright: ignore
            "dae_named_cluster.default")

    clusters = {
        conf["name"]: conf
        for conf in dask.config.get(  # pyright: ignore
            "dae_named_cluster.clusters")}
    cluster_config = clusters[cluster_name]
    return setup_client_from_config(
        cluster_config,
        number_of_workers=number_of_workers,
    )
