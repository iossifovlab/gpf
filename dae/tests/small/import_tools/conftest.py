# pylint: disable=W0621,C0114,C0116,C0415,W0212,W0613,C0302,C0115,W0102,W0603

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def resources_dir(request) -> Path:
    resources_path = os.path.join(
        os.path.dirname(os.path.realpath(request.module.__file__)),
        "resources")
    return Path(resources_path)
