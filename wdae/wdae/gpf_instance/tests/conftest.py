# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest


@pytest.fixture(scope="function")
def wgpf_instance_fixture(
        wgpf_instance, admin_client, remote_settings, global_dae_fixtures_dir):
    return wgpf_instance(global_dae_fixtures_dir)
