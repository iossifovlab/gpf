# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dask import config

import dae.dask.named_cluster

from dae.dask.named_cluster import setup_client, \
    setup_client_from_config


def test_default():
    client, _ = setup_client(number_of_threads=4)
    print(client)
    assert client


def test_config_access():
    with config.set({"dask.config.get": None}):
        client, _ = setup_client()
        assert client


def test_setup_cluster_from_config_simple(mocker):
    mocked_factory = mocker.patch(
        "dae.dask.named_cluster.set_up_local_cluster", autospec=True)
    mocker.patch.dict(
        dae.dask.named_cluster._CLUSTER_TYPES, {
            "local": mocked_factory
        }
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
        })
