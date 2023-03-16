# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines,no-member
import argparse
import textwrap

import pytest

import dask.distributed

import dae.dask.named_cluster
from dae.testing import setup_directories
from dae.task_graph import TaskGraphCli


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
