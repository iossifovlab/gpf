from dae.dask.named_cluster import setup_client
import dask.config as config


def test_default():
    client, _, _ = setup_client(number_of_threads=4)
    print(client)
    assert client


def test_config_access():
    with config.set({'dask.config.get': None}):
        client, _, _ = setup_client()
        assert client
