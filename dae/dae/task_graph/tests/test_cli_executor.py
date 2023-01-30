# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines,no-member
import argparse
import pytest

import dask.distributed
import dask_jobqueue

from dae.task_graph import TaskGraphCli


@pytest.mark.parametrize("argv", [
    [],
    ["-N", "local"],
    ["--dcn", "local"],
    ["--dask-cluster-name", "local"],
])
def test_cli_named_cluster_local(mocker, argv):
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(argv)

    mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)
    mocker.patch(
        "dask.distributed.LocalCluster",
        autospec=True)

    TaskGraphCli.create_executor(**vars(args))
    dask.distributed\
        .LocalCluster.assert_called_once_with()  # type: ignore


@pytest.mark.parametrize("argv", [
    ["-N", "sge_small"],
    ["--dcn", "sge_small"],
    ["--dask-cluster-name", "sge_small"],
])
def test_cli_named_cluster_sge_small(mocker, argv):
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(argv)

    mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)
    mocker.patch(
        "dask_jobqueue.SGECluster",
        autospec=True)

    TaskGraphCli.create_executor(**vars(args))
    dask_jobqueue\
        .SGECluster.assert_called_once_with(
            scheduler_options={"dashboard_address": ":8898"},
            cores=1, memory="1GB", log_directory="./sge_worker_logs"
        )  # type: ignore


@pytest.mark.parametrize("argv", [
    ["-N", "sge_large"],
    ["--dcn", "sge_large"],
    ["--dask-cluster-name", "sge_large"],
])
def test_cli_named_cluster_sge_large(mocker, argv):
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(argv)

    mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)
    mocker.patch(
        "dask_jobqueue.SGECluster",
        autospec=True)

    TaskGraphCli.create_executor(**vars(args))
    dask_jobqueue\
        .SGECluster.assert_called_once_with(
            scheduler_options={"dashboard_address": ":8898"},
            cores=1, memory="10GB", log_directory="./sge_worker_logs"
        )  # type: ignore
    # dask_jobqueue\
    #     .SGECluster.adapt.assert_called_once_with()
