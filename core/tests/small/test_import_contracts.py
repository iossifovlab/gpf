"""The import-linter contracts of ``core/.importlinter`` are kept.

The contracts fence gpf core off from the gpf_web apps. The CI gates the
build on the exit code of pytest only, so this test runs the contracts.
"""
import pathlib

from importlinter.cli import lint_imports

CONFIG = pathlib.Path(__file__).resolve().parents[2] / ".importlinter"


def test_import_contracts_are_kept() -> None:
    assert CONFIG.exists(), f"{CONFIG} is missing"

    # no_cache: pytest runs with xdist workers, and the import-linter
    # cache directory is not safe for parallel writes.
    assert lint_imports(config_filename=str(CONFIG), no_cache=True) == 0
