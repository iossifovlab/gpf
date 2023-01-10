# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.dask.client_factory import DaskClient


def test_from_dict_with_log_dir(tmpdir):
    args = {
        "jobs": 1,  # speeds up the test
        "log_dir": str(tmpdir)
    }

    client = DaskClient.from_dict(args)
    assert client is not None
    client.__exit__()
