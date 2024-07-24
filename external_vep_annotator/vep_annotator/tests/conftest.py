import os
from pathlib import Path

import pytest


@pytest.fixture()
def vep_fixtures() -> Path:
    return Path(
        os.path.dirname(os.path.realpath(__file__)), "fixtures",
    )
