# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines,no-member
import argparse
import pathlib
import textwrap

import dae.dask.named_cluster
import dask.distributed
import pytest
from dae.genomic_resources.testing import setup_directories
from dae.task_graph import TaskGraphCli
from pytest_mock import MockerFixture


@pytest.mark.parametrize("argv", [
    ["-c"],
    ["--dccf"],
    ["--dask-cluster-config-file"],
])
def test_cli_cluster_with_config_file(
        mocker: MockerFixture, argv: list[str],
        tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path / "cluster.yaml", textwrap.dedent("""
        name: special
        type: local
        number_of_threads: 20
        params:
            memory: 2GB
            scheduler_options:
                dashboard_address: :8898
        """),
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
            memory="2GB",
            threads_per_worker=1,
        )
    cluster_mock = dae.dask.named_cluster\
        .Client.call_args.args[0]  # type: ignore
    cluster_mock.scale.assert_called_once_with(n=20)
