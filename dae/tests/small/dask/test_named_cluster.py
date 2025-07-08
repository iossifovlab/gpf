# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any

import dae.dask.named_cluster
import pytest
import pytest_mock
from dae.dask.named_cluster import setup_client, setup_client_from_config
from dask import config


@pytest.fixture
def named_cluster_config() -> dict[str, Any]:
    return {
        "default": "local",
        "clusters": [{
            "name": "local",
            "type": "local",
            "params": {
                "memory_limit": "4GB",
                "threads_per_worker": 2,
            },
        },

        ],
    }


def test_default(
    mocker: pytest_mock.MockerFixture,
    named_cluster_config: dict[str, Any],
) -> None:
    mocked_local = mocker.patch(
        "dask.distributed.LocalCluster", autospec=True)

    mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)

    with config.set({"dae_named_cluster": named_cluster_config}):
        client, _ = setup_client()
        assert client

    assert mocked_local.call_count == 1
    assert mocked_local.call_args.kwargs == {
        "memory_limit": "4GB",
        "threads_per_worker": 2,
    }


def test_default_with_number_of_threads(
    mocker: pytest_mock.MockerFixture,
    named_cluster_config: dict[str, Any],
) -> None:
    mocked_local = mocker.patch(
        "dask.distributed.LocalCluster", autospec=True)
    mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)

    with config.set({"dae_named_cluster": named_cluster_config}):
        client, _ = setup_client(number_of_threads=4)
        assert client

    assert mocked_local.call_count == 1
    assert mocked_local.call_args.kwargs["n_workers"] == 1


def test_config_access(
    mocker: pytest_mock.MockerFixture,
    named_cluster_config: dict[str, Any],
) -> None:
    mocked_local = mocker.patch(
        "dask.distributed.LocalCluster", autospec=True)
    mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)
    with config.set({"dae_named_cluster": named_cluster_config}):
        client, _ = setup_client()
        assert client

    assert mocked_local.call_count == 1
    assert mocked_local.call_args.kwargs == {
        "memory_limit": "4GB",
        "threads_per_worker": 2,
    }


def test_setup_cluster_from_config_simple(
    mocker: pytest_mock.MockerFixture,
) -> None:
    mocked_factory = mocker.patch(
        "dae.dask.named_cluster.set_up_local_cluster", autospec=True)
    mocker.patch.dict(
        dae.dask.named_cluster._CLUSTER_TYPES, {
            "local": mocked_factory,
        },
    )
    mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)

    setup_client_from_config({
        "type": "local",
    }, number_of_threads_param=2)

    # pylint: disable=no-member
    dae.dask.named_cluster\
        .set_up_local_cluster.assert_called_once_with({  # type: ignore
            "number_of_workers": 2,
        })


def test_setup_sge_cluster(mocker: pytest_mock.MockerFixture) -> None:
    mocked_sge = mocker.patch(
        "dask_jobqueue.SGECluster", autospec=True)

    mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)

    setup_client_from_config({
        "type": "sge",
    }, number_of_threads_param=2)

    assert mocked_sge.call_count == 1
    assert "number_of_workers" not in mocked_sge.call_args.kwargs


def test_setup_slurm_cluster(mocker: pytest_mock.MockerFixture) -> None:
    mocked_slurm = mocker.patch(
        "dask_jobqueue.SLURMCluster", autospec=True)

    mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)

    setup_client_from_config({
        "type": "slurm",
    }, number_of_threads_param=2)

    assert mocked_slurm.call_count == 1
    assert "number_of_workers" not in mocked_slurm.call_args.kwargs


def test_setup_manual_client(mocker: pytest_mock.MockerFixture) -> None:
    mocked_client = mocker.patch(
        "dae.dask.named_cluster.Client",
        autospec=True)

    setup_client_from_config({
        "type": "manual",
        "params": {
            "scheduler_address": "tcp://localhost:8786",
        },
    }, number_of_threads_param=2)

    assert mocked_client.call_count == 1

    assert mocked_client.call_args.args == (
        "tcp://localhost:8786",
    )
