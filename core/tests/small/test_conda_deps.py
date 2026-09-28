# pylint: disable=W0621,C0116
"""The committed conda environment file matches the workspace pyprojects.

``environment.yml`` is rendered by ``scripts/conda_env.py``; the guard
below fails whenever the committed file is stale. The remaining tests pin
the rendering rules on a throwaway workspace.
"""
import importlib.util
import pathlib
import re
import sys
from collections.abc import Iterable, Mapping
from types import ModuleType

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "conda_env.py"

REGENERATE = (
    "run `python scripts/conda_env.py` from the repo root and commit "
    "the result")

MEMBERS = {
    "core": "gpf-core",
    "web_api": "gpf-web",
    "federation": "gpf-federation",
    "rest_client": "gpf-rest-client",
}


@pytest.fixture(scope="module")
def conda_env() -> ModuleType:
    if not SCRIPT.exists():
        pytest.fail(f"{SCRIPT} is missing; the CI image must copy it")
    spec = importlib.util.spec_from_file_location("conda_env", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_committed_environment_file_is_current(
    conda_env: ModuleType,
) -> None:
    rendered = conda_env.render_all()
    assert set(rendered) == {"environment.yml"}

    for filename, text in rendered.items():
        committed = REPO_ROOT / filename
        if not committed.exists():
            pytest.fail(f"{committed} is missing; {REGENERATE}")
        assert committed.read_text() == text, (
            f"{committed} is stale; {REGENERATE}")


def test_table_entries_carry_a_reason(conda_env: ModuleType) -> None:
    for table in (conda_env.PIP_ONLY, conda_env.OMITTED):
        assert [
            name for name, reason in table.items() if not reason.strip()
        ] == []


def _pyproject(
    name: str,
    deps: Iterable[str],
    requires_python: str = ">=3.12",
) -> str:
    listed = "".join(f"    {dep!r},\n" for dep in deps)
    return (
        f'[project]\nname = "{name}"\n'
        f'requires-python = "{requires_python}"\n'
        f"dependencies = [\n{listed}]\n")


def _workspace(
    root: pathlib.Path,
    *,
    requires_python: str = ">=3.12",
    **deps: list[str],
) -> pathlib.Path:
    """Write a gpf-shaped workspace; ``deps`` are keyed by member dir."""
    sources = "".join(
        f"{name} = {{ workspace = true }}\n" for name in MEMBERS.values())
    (root / "pyproject.toml").write_text(
        _pyproject("gpf-monorepo", []) + "[tool.uv.sources]\n" + sources)
    for directory, name in MEMBERS.items():
        (root / directory).mkdir(parents=True, exist_ok=True)
        (root / directory / "pyproject.toml").write_text(
            _pyproject(name, deps.get(directory, []), requires_python))
    return root


def _render(
    conda_env: ModuleType,
    root: pathlib.Path,
    *,
    pip_only: Mapping[str, str] | None = None,
    conda_names: Mapping[str, str] | None = None,
) -> str:
    rendered = conda_env.render_all(
        root, pip_only=pip_only or {}, conda_names=conda_names or {})
    return str(rendered["environment.yml"])


def _dependencies(rendered: str) -> list[str]:
    return rendered.split("dependencies:\n", 1)[1].splitlines()


def _section(member: str) -> str:
    return (
        f"  # {MEMBERS[member]} ({member}/pyproject.toml "
        f"[project.dependencies])")


def test_render_maps_sorts_and_sections(
    conda_env: ModuleType, tmp_path: pathlib.Path,
) -> None:
    root = _workspace(
        tmp_path,
        requires_python=">=3.13",
        core=[
            "pyBigWig>=0.3", "dask>=2026.1", "duckdb>=1.5,<2", "apsw",
            "matplotlib>=3.8",
        ],
        web_api=["gpf-core", "django>=5.2,<5.3", "docker>=7.1"],
        federation=["gpf-core", "gpf-web", "ijson>=3.2"],
        rest_client=["gpf-web", "requests>=2.32"],
    )

    rendered = _render(conda_env, root, conda_names=conda_env.CONDA_NAMES)

    assert _dependencies(rendered) == [
        "  - python>=3.13",
        _section("core"),
        "  - apsw",
        "  - dask-core>=2026.1",
        "  - matplotlib-base>=3.8",
        "  - pybigwig>=0.3",
        "  - python-duckdb>=1.5,<2",
        _section("web_api"),
        "  - django>=5.2,<5.3",
        "  - docker-py>=7.1",
        _section("federation"),
        "  - ijson>=3.2",
        _section("rest_client"),
        "  - requests>=2.32",
    ]
    assert "name: gpf\n" in rendered
    assert "channels:\n  - conda-forge\n  - bioconda\n" in rendered


def test_gain_core_is_omitted_and_the_header_says_how_to_install_it(
    conda_env: ModuleType, tmp_path: pathlib.Path,
) -> None:
    root = _workspace(
        tmp_path, core=["gain-core", "numpy"], web_api=["gain-core"])

    rendered = _render(conda_env, root)

    assert "gain-core" not in "\n".join(_dependencies(rendered))
    header = rendered.split("name: gpf\n", 1)[0]
    assert f"# gain-core: {conda_env.OMITTED['gain-core']}\n" in header


def test_header_names_no_omitted_package_the_feeds_do_not_declare(
    conda_env: ModuleType, tmp_path: pathlib.Path,
) -> None:
    root = _workspace(tmp_path, core=["numpy"])

    rendered = _render(conda_env, root)

    assert "gain-core" not in rendered


def test_two_sources_merge_into_one_line(
    conda_env: ModuleType, tmp_path: pathlib.Path,
) -> None:
    root = _workspace(
        tmp_path,
        core=["pyyaml>=6", "numpy>=2", "scipy>=1,<2", "requests>=2.32"],
        web_api=["PyYAML", "numpy<3", "scipy>=1"],
        rest_client=["requests>=2.32"],
    )

    deps = _dependencies(_render(conda_env, root))

    assert [d for d in deps if "pyyaml" in d] == ["  - pyyaml>=6"]
    assert [d for d in deps if "numpy" in d] == ["  - numpy>=2,<3"]
    assert [d for d in deps if "scipy" in d] == ["  - scipy>=1,<2"]
    assert [d for d in deps if "requests" in d] == ["  - requests>=2.32"]
    # A section that adds nothing new keeps only its heading.
    assert deps[-1] == _section("rest_client")


def test_clauses_keep_their_written_order(
    conda_env: ModuleType, tmp_path: pathlib.Path,
) -> None:
    root = _workspace(
        tmp_path,
        requires_python="<3.15,>=3.12",
        core=["numpy<3,>=2,!=2.5", "scipy (!=1.5, <2, >=1)"],
    )

    deps = _dependencies(_render(conda_env, root))

    assert deps[0] == "  - python<3.15,>=3.12"
    assert "  - numpy<3,>=2,!=2.5" in deps
    assert "  - scipy!=1.5,<2,>=1" in deps


@pytest.mark.parametrize("requirement", [
    'foo>=1; sys_platform == "win32"',
    "foo[bar]>=1",
    "foo @ https://example.com/foo-1.0.tar.gz",
    "foo===1.0",
])
def test_unmodelled_requirement_raises(
    conda_env: ModuleType, tmp_path: pathlib.Path, requirement: str,
) -> None:
    root = _workspace(tmp_path, core=[requirement])

    with pytest.raises(ValueError, match="does not model"):
        _render(conda_env, root)


def test_pip_only_dependency_renders_under_pip(
    conda_env: ModuleType, tmp_path: pathlib.Path,
) -> None:
    root = _workspace(tmp_path, core=["numpy"], federation=["ijson>=3.2"])

    rendered = _render(conda_env, root, pip_only={"ijson": "not on conda"})

    assert rendered.endswith(
        f"{_section('federation')}\n"
        f"{_section('rest_client')}\n"
        "  # pip-only: PIP_ONLY in scripts/conda_env.py\n"
        "  - pip\n"
        "  - pip:\n"
        "    # ijson: not on conda\n"
        "    - ijson>=3.2\n")


def test_no_pip_block_without_pip_only_dependencies(
    conda_env: ModuleType, tmp_path: pathlib.Path,
) -> None:
    root = _workspace(tmp_path, core=["numpy"], federation=["ijson>=3.2"])

    deps = _dependencies(_render(conda_env, root))

    assert "  - pip" not in deps
    assert "  - pip:" not in deps
    assert "  - ijson>=3.2" in deps


def test_undeclared_pip_only_entry_raises(
    conda_env: ModuleType, tmp_path: pathlib.Path,
) -> None:
    root = _workspace(tmp_path, core=["numpy"])

    with pytest.raises(
            ValueError, match=re.escape("PIP_ONLY entries no feed declares")):
        _render(conda_env, root, pip_only={"ijson": "not on conda"})


def test_undeclared_conda_name_raises(
    conda_env: ModuleType, tmp_path: pathlib.Path,
) -> None:
    root = _workspace(tmp_path, core=["dask>=2026.1"])

    with pytest.raises(
            ValueError,
            match=re.escape("CONDA_NAMES entries no feed declares: brotli")):
        _render(conda_env, root, conda_names={
            "brotli": "brotli-python", "dask": "dask-core"})


def _declaring_everything(conda_env: ModuleType) -> list[str]:
    """Return runtime deps declaring every real table entry.

    ``main`` renders with the real tables, which refuse a workspace that
    leaves any of their entries undeclared.
    """
    return [*conda_env.CONDA_NAMES, *conda_env.PIP_ONLY]


@pytest.mark.parametrize("rest_client", [
    ["gunicorn>=22", "requests>=2.32"],  # added
    ["gunicorn>=23"],                    # changed
    [],                                  # removed
])
def test_check_reports_drift_without_rewriting(
    conda_env: ModuleType, tmp_path: pathlib.Path,
    rest_client: list[str],
) -> None:
    everything = _declaring_everything(conda_env)
    root = _workspace(
        tmp_path, core=everything, rest_client=["gunicorn>=22"])
    assert conda_env.main([], root=root) == 0
    assert conda_env.main(["--check"], root=root) == 0

    _workspace(tmp_path, core=everything, rest_client=rest_client)
    before = (root / "environment.yml").read_text()

    assert conda_env.main(["--check"], root=root) == 1
    assert (root / "environment.yml").read_text() == before


def test_check_reports_a_missing_file(
    conda_env: ModuleType, tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path, core=_declaring_everything(conda_env))

    assert conda_env.main(["--check"], root=root) == 1

    assert "environment.yml is stale" in capsys.readouterr().err
    assert not (root / "environment.yml").exists()


def test_rendered_file_parses_as_a_conda_environment(
    conda_env: ModuleType, tmp_path: pathlib.Path,
) -> None:
    root = _workspace(
        tmp_path, core=["numpy>=2", "ijson>=3.2"], web_api=["django"])

    rendered = _render(conda_env, root, pip_only={"ijson": "not on conda"})

    assert yaml.safe_load(rendered) == {
        "name": "gpf",
        "channels": ["conda-forge", "bioconda"],
        "dependencies": [
            "python>=3.12", "numpy>=2", "django", "pip",
            {"pip": ["ijson>=3.2"]},
        ],
    }
