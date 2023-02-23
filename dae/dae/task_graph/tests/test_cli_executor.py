# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines,no-member
import argparse
import textwrap

import pytest

import dask.distributed
import dask_jobqueue

import dae.dask.named_cluster
from dae.testing import setup_directories
from dae.task_graph import TaskGraphCli


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
            cores=1, memory="1GB", log_directory="./.sge_worker_logs",
            walltime="24:00:00"
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
            cores=1, memory="10GB", log_directory="./.sge_worker_logs",
            walltime="72:00:00"
        )  # type: ignore

    cluster_mock = dae.dask.named_cluster\
        .Client.call_args.args[0]  # type: ignore
    cluster_mock.adapt.assert_called_once_with(minimum=3, maximum=200)


@pytest.mark.parametrize("argv", [
    ["-N", "slurm"],
    ["--dcn", "slurm"],
    ["--dask-cluster-name", "slurm"],
])
def test_cli_named_cluster_slurm(mocker, argv):
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    args = parser.parse_args(argv)

    mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)
    mocker.patch(
        "dask_jobqueue.SLURMCluster",
        autospec=True)

    TaskGraphCli.create_executor(**vars(args))
    dask_jobqueue\
        .SLURMCluster.assert_called_once_with(
            cores=1, memory="1GB", log_directory="./slurm_worker_logs"
        )  # type: ignore

    cluster_mock = dae.dask.named_cluster\
        .Client.call_args.args[0]  # type: ignore
    cluster_mock.scale.assert_called_once_with(n=10)


@pytest.mark.parametrize("argv", [
    ["-c"],
    ["--dccf"],
    ["--dask-cluster-config-file"],
])
def test_cli_cluster_with_config_file(mocker, argv, tmp_path):
    setup_directories(
        tmp_path / "cluster.yaml", textwrap.dedent("""
        name: special
        type: local
        number_of_threads: 20
        params:
            cores: 1
            memory: 2GB
            scheduler_options:
                dashboard_address: :8898
        """)
    )
    parser = argparse.ArgumentParser(description="test_basic")
    TaskGraphCli.add_arguments(parser)
    argv.append(str(tmp_path / "cluster.yaml"))

    args = parser.parse_args(argv)

    mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)
    mocker.patch(
        "dask.distributed.LocalCluster",
        autospec=True)

    TaskGraphCli.create_executor(**vars(args))

    dask.distributed\
        .LocalCluster.assert_called_once_with(  # type: ignore
            scheduler_options={"dashboard_address": ":8898"},
            cores=1, memory="2GB")
    cluster_mock = dae.dask.named_cluster\
        .Client.call_args.args[0]  # type: ignore
    cluster_mock.scale.assert_called_once_with(n=20)
