# pylint: disable=redefined-outer-name,C0114,C0115,C0116,protected-access

import os
import shutil
import tempfile

import pytest


def relative_to_this_test_folder(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.fixture(scope="session")
def fixture_path():
    def builder(relpath):
        return relative_to_this_test_folder(os.path.join("fixtures", relpath))

    return builder


@pytest.fixture()
def local_fixture():
    def builder(relpath):
        return relative_to_this_test_folder(os.path.join("fixtures", relpath))
    return builder


@pytest.fixture(scope="function")
def temp_cache_dir(request):
    temp_directory = tempfile.mkdtemp(prefix="cache_repo_", suffix="_test")

    def fin():
        shutil.rmtree(temp_directory)

    request.addfinalizer(fin)

    return temp_directory
