"""The import-linter contracts of ``core/.importlinter`` are kept.

The ``forbidden`` contract fences gpf core off from the gpf_web apps. The
``acyclic_siblings`` contract stops a new import cycle among the direct
subpackages of ``gpf``. Its ``ignore_imports`` list is the baseline of the
cycles of today. The CI gates the build on the exit code of pytest only, so
this test runs the contracts.
"""
import logging
import pathlib
import subprocess
import sys

CONFIG = pathlib.Path(__file__).resolve().parents[2] / ".importlinter"

# lint_imports runs in a child process. In the pytest process, it calls
# logging.config.dictConfig, which disables every existing logger and
# breaks later caplog tests, and it changes sys.path.
# no_cache: pytest runs with xdist workers, and the import-linter cache
# directory is not safe for parallel writes.
_LINT_IMPORTS = (
    "import sys\n"
    "from importlinter.cli import lint_imports\n"
    "sys.exit(lint_imports(config_filename=sys.argv[1], no_cache=True))\n"
)


def _run_import_linter() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", _LINT_IMPORTS, str(CONFIG)],
        cwd=CONFIG.parent,
        capture_output=True,
        text=True,
        check=False,
    )


def test_import_contracts_are_kept() -> None:
    assert CONFIG.exists(), f"{CONFIG} is missing"

    result = _run_import_linter()

    assert result.returncode == 0, result.stdout + result.stderr


def test_import_linter_run_leaves_the_process_state_alone() -> None:
    """The linter run keeps the loggers and sys.path of pytest intact."""
    logger = logging.getLogger("gpf.test_import_contracts.probe")
    sys_path = list(sys.path)

    _run_import_linter()

    assert not logger.disabled
    assert sys.path == sys_path
