"""Architecture tests for gain package using pytestarch."""
import os

import pytest
from pytestarch import EvaluableArchitecture, get_evaluable_architecture

GAIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAIN_SRC = os.path.join(GAIN_ROOT, "gain")
TESTS_SRC = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="module")
def gain_arch() -> EvaluableArchitecture:
    return get_evaluable_architecture(
        GAIN_SRC,
        GAIN_SRC,
        exclude_external_libraries=False,
    )


@pytest.fixture(scope="module")
def gain_tests_arch() -> EvaluableArchitecture:
    return get_evaluable_architecture(
        TESTS_SRC,
        TESTS_SRC,
        exclude_external_libraries=False,
    )


def test_gain_core_does_not_import_from_gpf_core(
    gain_arch: EvaluableArchitecture,
) -> None:
    """gain_core (gain package) must not import from gpf_core (gpf package)."""
    gpf_imports = [
        module
        for module in gain_arch.modules
        if module == "gpf" or module.startswith("gpf.")
    ]
    assert gpf_imports == [], (
        f"gain_core must not import from gpf_core, but found: {gpf_imports}"
    )


def test_gain_core_tests_do_not_import_from_gpf_core(
    gain_tests_arch: EvaluableArchitecture,
) -> None:
    """gain_core tests must not import from gpf_core (gpf package)."""
    gpf_imports = [
        module
        for module in gain_tests_arch.modules
        if module == "gpf" or module.startswith("gpf.")
    ]
    assert gpf_imports == [], (
        f"gain_core tests must not import from gpf_core, "
        f"but found: {gpf_imports}"
    )
