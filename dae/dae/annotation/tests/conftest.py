# pylint: disable=W0621,C0114,C0116,W0212,W0613

import os
from typing import Callable
import pytest


def relative_to_this_test_folder(path: str) -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.fixture(scope="session")
def work_dir() -> str:
    return relative_to_this_test_folder("fixtures")


@pytest.fixture
def annotation_config(fixture_dirname: Callable[[str], str]) -> str:
    return fixture_dirname("annotation.yaml")
