# pylint: disable=redefined-outer-name,C0114,C0115,C0116,protected-access

import os
from collections.abc import Callable

import pytest


def relative_to_this_test_folder(path: str) -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.fixture(scope="session")
def fixture_path() -> Callable[[str], str]:

    def builder(relpath: str) -> str:
        return relative_to_this_test_folder(os.path.join("fixtures", relpath))

    return builder


@pytest.fixture
def local_fixture() -> Callable[[str], str]:

    def builder(relpath: str) -> str:
        return relative_to_this_test_folder(os.path.join("fixtures", relpath))

    return builder
