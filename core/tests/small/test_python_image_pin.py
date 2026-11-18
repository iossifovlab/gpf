# pylint: disable=W0621,C0116
"""The CI images name their Python interpreter in one place (gpf#1173).

The ``environment`` block of the root ``Jenkinsfile`` names the CI
interpreter as ``PYTHON_IMAGE``, and each CI ``docker build`` passes it
with ``--build-arg``. The guard below reads the source tree and fails
when a Dockerfile names a literal ``python:`` image in a ``FROM`` line,
or when the default of its ``ARG PYTHON_IMAGE`` differs from the
``Jenkinsfile`` value. The guard also fails when the ``PYTHON_IMAGE`` of
``web_e2e/Jenkinsfile.e2e`` differs from the ``Jenkinsfile`` value.

The ``core`` CI image holds the ``Jenkinsfile``, but not the other
Dockerfiles or ``web_e2e/Jenkinsfile.e2e``. When a file that a check
reads is not in the tree, the check skips with a reason. The checkout
run of the guard is the proof.
"""
import os
import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
JENKINSFILE = REPO_ROOT / "Jenkinsfile"
E2E_JENKINSFILE = REPO_ROOT / "web_e2e" / "Jenkinsfile.e2e"

# The Dockerfiles that the guard does not check, relative to the repo
# root. They build the production images, which gpf#1175 moves to the
# CI interpreter. gpf#1175 removes them from this list.
EXEMPT_DOCKERFILES = [
    "Dockerfile.production",
    "web_api/Dockerfile.production",
]

# The CI Dockerfiles that gpf#1173 names. The walk must find each one.
NAMED_CI_DOCKERFILES = [
    "core/Dockerfile",
    "federation/Dockerfile",
    "rest_client/Dockerfile",
    "web_api/Dockerfile",
]

# The directories that hold no Dockerfile of the repo.
SKIPPED_DIRS = {"node_modules", "__pycache__", "dist"}


def is_literal_python_image(image: str) -> bool:
    """Tell if ``image`` names the ``python`` image of a registry.

    The image can carry a registry prefix, for example
    ``docker.io/library/python:3.12-slim``.
    """
    name = image.split("@", 1)[0].rsplit("/", 1)[-1]
    return name.split(":", 1)[0] == "python"


def literal_python_from_lines(dockerfile: str) -> list[str]:
    """Return the ``FROM`` lines that name a literal ``python`` image.

    The guard skips the ``--platform`` flag and the other flags of a
    ``FROM`` line before it reads the image.
    """
    found: list[str] = []
    for line in dockerfile.splitlines():
        words = line.split()
        if not words or words[0].upper() != "FROM":
            continue
        images = [word for word in words[1:] if not word.startswith("--")]
        if images and is_literal_python_image(images[0]):
            found.append(line.strip())
    return found


ARG_PYTHON_IMAGE = re.compile(r"^\s*ARG\s+PYTHON_IMAGE=(\S+)", re.MULTILINE)


def arg_default_mismatches(dockerfile: str, expected: str) -> list[str]:
    """Return the ``ARG PYTHON_IMAGE`` lines whose default is not
    ``expected``."""
    return [
        match.group(0).strip()
        for match in ARG_PYTHON_IMAGE.finditer(dockerfile)
        if match.group(1) != expected]


JENKINS_PYTHON_IMAGE = re.compile(
    r"""^\s*PYTHON_IMAGE\s*=\s*['"]([^'"]+)['"]""", re.MULTILINE)


def jenkins_python_image(jenkinsfile: str) -> str:
    """Return the ``PYTHON_IMAGE`` value of a Jenkinsfile.

    Raise ``ValueError`` unless the value stands on exactly one line.
    """
    values = JENKINS_PYTHON_IMAGE.findall(jenkinsfile)
    if len(values) != 1:
        raise ValueError(f"expected one PYTHON_IMAGE line, found {values}")
    return str(values[0])


def read_or_skip(path: pathlib.Path) -> str:
    if not path.exists():
        pytest.skip(f"{path} is not in this tree; a checkout runs the check")
    return path.read_text()


def ci_dockerfiles(root: pathlib.Path) -> dict[str, str]:
    """Map each Dockerfile under ``root`` that the guard checks to its text.

    The keys are paths relative to ``root``. The map leaves out the
    ``EXEMPT_DOCKERFILES``.
    """
    found: dict[str, str] = {}
    for top, dirs, files in os.walk(root):
        dirs[:] = [
            name for name in dirs
            if not name.startswith(".") and name not in SKIPPED_DIRS]
        for name in files:
            path = pathlib.Path(top) / name
            rel = path.relative_to(root).as_posix()
            if name.startswith("Dockerfile") and \
                    rel not in EXEMPT_DOCKERFILES:
                found[rel] = path.read_text()
    return found


def ci_dockerfiles_or_skip() -> dict[str, str]:
    """Return the CI Dockerfiles of the tree, or skip.

    The check skips when a named CI Dockerfile is not in the tree, as in
    the ``core`` CI image.
    """
    found = ci_dockerfiles(REPO_ROOT)
    missing = sorted(set(NAMED_CI_DOCKERFILES) - found.keys())
    if missing:
        pytest.skip(
            f"{', '.join(missing)} not in this tree; a checkout runs the "
            f"check")
    return found


@pytest.fixture(name="ci_python_image")
def fixture_ci_python_image() -> str:
    return jenkins_python_image(read_or_skip(JENKINSFILE))


def test_literal_python_from_line_is_reported() -> None:
    dockerfile = "ARG X=1\nFROM python:3.12-slim\nRUN true\n"

    assert literal_python_from_lines(dockerfile) == [
        "FROM python:3.12-slim"]


@pytest.mark.parametrize("line", [
    "FROM --platform=linux/amd64 python:3.12-slim",
    "FROM docker.io/library/python:3.12-slim AS base",
    "FROM python@sha256:0123",
])
def test_literal_python_from_line_with_a_flag_or_a_registry_is_reported(
    line: str,
) -> None:
    dockerfile = f"ARG X=1\n{line}\nRUN true\n"

    assert literal_python_from_lines(dockerfile) == [line]


@pytest.mark.parametrize("line", [
    "FROM ${PYTHON_IMAGE}",
    "FROM ${PYTHON_IMAGE} AS runtime",
    "FROM mambaorg/micromamba:2.3.2",
    "FROM  mcr.microsoft.com/playwright:v1.55.1-jammy",
])
def test_from_line_without_a_literal_python_image_is_not_reported(
    line: str,
) -> None:
    assert not literal_python_from_lines(f"{line}\n")


def test_arg_default_that_differs_from_the_jenkinsfile_is_reported() -> None:
    dockerfile = "ARG PYTHON_IMAGE=python:3.12-slim\nFROM ${PYTHON_IMAGE}\n"

    assert arg_default_mismatches(dockerfile, "python:3.13-slim") == [
        "ARG PYTHON_IMAGE=python:3.12-slim"]


def test_arg_default_that_matches_the_jenkinsfile_is_not_reported() -> None:
    dockerfile = "ARG PYTHON_IMAGE=python:3.13-slim\nFROM ${PYTHON_IMAGE}\n"

    assert arg_default_mismatches(dockerfile, "python:3.13-slim") == []


def test_jenkins_python_image_reads_the_environment_line() -> None:
    jenkinsfile = (
        "environment {\n"
        '    CI_TAG = "x"\n'
        "    PYTHON_IMAGE = 'python:3.13-slim'\n"
        "}\n")

    assert jenkins_python_image(jenkinsfile) == "python:3.13-slim"


def test_jenkins_python_image_needs_exactly_one_line() -> None:
    jenkinsfile = (
        "    PYTHON_IMAGE = 'python:3.13-slim'\n"
        "    PYTHON_IMAGE = 'python:3.12-slim'\n")

    with pytest.raises(ValueError, match="expected one PYTHON_IMAGE line"):
        jenkins_python_image(jenkinsfile)


def test_ci_dockerfiles_leave_out_the_exempt_dockerfiles(
    tmp_path: pathlib.Path,
) -> None:
    for rel in [*EXEMPT_DOCKERFILES, "core/Dockerfile"]:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("FROM python:3.12-slim\n")

    assert sorted(ci_dockerfiles(tmp_path)) == ["core/Dockerfile"]


def test_exempt_dockerfiles_exist() -> None:
    missing = [
        name for name in EXEMPT_DOCKERFILES
        if not (REPO_ROOT / name).exists()]
    if len(missing) == len(EXEMPT_DOCKERFILES):
        pytest.skip("no exempt Dockerfile in this tree; a checkout runs "
                    "the check")

    assert missing == []


def test_no_ci_dockerfile_names_a_literal_python_image() -> None:
    found = {
        name: lines
        for name, text in ci_dockerfiles_or_skip().items()
        if (lines := literal_python_from_lines(text))}

    assert found == {}


def test_ci_dockerfile_defaults_match_the_jenkinsfile(
    ci_python_image: str,
) -> None:
    found = {
        name: lines
        for name, text in ci_dockerfiles_or_skip().items()
        if (lines := arg_default_mismatches(text, ci_python_image))}

    assert found == {}


def test_named_ci_dockerfiles_read_the_python_image_arg(
    ci_python_image: str,
) -> None:
    dockerfiles = ci_dockerfiles_or_skip()

    missing = [
        name for name in NAMED_CI_DOCKERFILES
        if f"ARG PYTHON_IMAGE={ci_python_image}" not in dockerfiles[name]
        or "FROM ${PYTHON_IMAGE}" not in dockerfiles[name]]

    assert missing == []


def test_e2e_jenkinsfile_names_the_same_python_image(
    ci_python_image: str,
) -> None:
    e2e = jenkins_python_image(read_or_skip(E2E_JENKINSFILE))

    assert e2e == ci_python_image
