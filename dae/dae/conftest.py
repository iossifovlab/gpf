# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

pytest_plugins = ["dae_conftests.dae_conftests"]


class DummyFuture:
    """Dummy Dask future object for testing."""

    def __init__(self, func, *args):
        self._result = None
        self._exception = None

        self.func = func
        self.args = args

    def run(self):
        try:
            self._result = self.func(*self.args)
        except Exception as ex:  # pylint: disable=broad-except
            self._exception = ex

    def done(self):
        return self._result is not None or self._exception is not None

    def result(self):
        return self._result

    def exception(self):
        return self._exception


class DummyClient:
    """Dummy Dask client for testing."""

    def __init__(self, **kwargs):
        print("DUMMY CLIENT CREATED...")
        self.tasks = []

    @staticmethod
    def from_dict(kwargs):
        return DummyClient(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass

    @staticmethod
    def submit(func, *args):
        return DummyFuture(func, *args)


def dummy_as_completed(futures):
    for future in futures:
        future.run()
        yield future


@pytest.fixture
def dask_mocker(mocker):

    mocker.patch(
        "dae.dask.client_factory.DaskClient.from_dict",
        DummyClient.from_dict)

    mocker.patch(
        "dae.genomic_resources.histogram.as_completed",
        dummy_as_completed)
