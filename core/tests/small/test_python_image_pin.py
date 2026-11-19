# pylint: disable=W0621,C0116
"""The images name their Python interpreter in one place.

The ``environment`` block of the root ``Jenkinsfile`` names the
interpreter as ``PYTHON_IMAGE`` (gpf#1173). Each CI ``docker build`` and
each production ``docker build`` passes it with ``--build-arg``
(gpf#1175). The guard below reads the source tree and fails when a
Dockerfile names a literal ``python:`` image in a ``FROM`` line, or when
the default of its ``ARG PYTHON_IMAGE`` differs from the ``Jenkinsfile``
value. The guard also fails when the ``PYTHON_IMAGE`` of
``web_e2e/Jenkinsfile.e2e`` or the pip2pi container of
``Jenkinsfile.release`` differs from the ``Jenkinsfile`` value.

``Jenkinsfile.python-matrix`` names an interpreter on purpose: each cell
builds with ``--build-arg PYTHON_IMAGE=python:${PY}-slim`` (gpf#1174).
The guard checks that its ``PY`` axis holds the version of the
``Jenkinsfile`` value, so the matrix keeps the default interpreter.

The ``core`` CI image holds the ``Jenkinsfile``, but not the other
Dockerfiles, ``web_e2e/Jenkinsfile.e2e`` or ``Jenkinsfile.release``.
When a file that a check reads is not in the tree, the check skips with
a reason. The checkout run of the guard is the proof.
"""
import os
import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
JENKINSFILE = REPO_ROOT / "Jenkinsfile"
E2E_JENKINSFILE = REPO_ROOT / "web_e2e" / "Jenkinsfile.e2e"
RELEASE_JENKINSFILE = REPO_ROOT / "Jenkinsfile.release"
MATRIX_JENKINSFILE = REPO_ROOT / "Jenkinsfile.python-matrix"
MATRIX_JOB_DSL = REPO_ROOT / "jenkins-jobs" / "python_matrix.groovy"

# The CI Dockerfiles that gpf#1173 names. The walk must find each one.
NAMED_CI_DOCKERFILES = [
    "core/Dockerfile",
    "federation/Dockerfile",
    "rest_client/Dockerfile",
    "web_api/Dockerfile",
]

# The production Dockerfiles that gpf#1175 names. The walk must find
# each one.
NAMED_PRODUCTION_DOCKERFILES = [
    "Dockerfile.production",
    "web_api/Dockerfile.production",
]

NAMED_DOCKERFILES = [*NAMED_CI_DOCKERFILES, *NAMED_PRODUCTION_DOCKERFILES]

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


ARG_PYTHON_IMAGE = re.compile(
    r"^\s*ARG\s+PYTHON_IMAGE\b(?:=(\S*))?.*$", re.MULTILINE)


def arg_default_mismatches(dockerfile: str, expected: str) -> list[str]:
    """Return the ``ARG PYTHON_IMAGE`` lines whose default is not
    ``expected``.

    A bare ``ARG PYTHON_IMAGE`` has no default, so the guard reports it
    too: a build without ``--build-arg`` would fail on it.
    """
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


LITERAL_PYTHON_IMAGE = re.compile(r"(?<![\w${/.-])python[:@]")
LITERAL_PYTHON_IMAGE_WORD = re.compile(r"(?<![\w${/.-])python[:@][^\s'\"]+")


def is_comment(line: str) -> bool:
    return line.strip().startswith(("//", "#"))


def literal_python_image_lines(jenkinsfile: str) -> list[str]:
    """Return the stripped Jenkinsfile lines that name a literal
    ``python`` image.

    The guard skips comment lines and the ``PYTHON_IMAGE`` declaration.
    """
    found: list[str] = []
    for line in jenkinsfile.splitlines():
        if is_comment(line) or JENKINS_PYTHON_IMAGE.match(line):
            continue
        if LITERAL_PYTHON_IMAGE.search(line):
            found.append(line.strip())
    return found


def literal_python_image_mismatches(
    jenkinsfile: str, expected: str,
) -> list[str]:
    """Return the stripped Jenkinsfile lines that name a literal
    ``python`` image other than ``expected``.

    The guard skips comment lines and the ``PYTHON_IMAGE`` declaration.
    """
    return [
        line for line in literal_python_image_lines(jenkinsfile)
        if any(image != expected
               for image in LITERAL_PYTHON_IMAGE_WORD.findall(line))]


# The directories of the CI Dockerfiles, and the ``runProject()``
# parameter that names one of them.
CI_DOCKERFILE_DIRS = {
    *(name.split("/", 1)[0] for name in NAMED_CI_DOCKERFILES), "${name}"}

DOCKER_BUILD_FILE = re.compile(r"-f\s+(\S+)/Dockerfile(?=\s|$)")
DOCKER_BUILD_PRODUCTION_FILE = re.compile(
    r"-f\s+(\S*Dockerfile\.production)(?=\s|$)")
PYTHON_IMAGE_BUILD_ARG = re.compile(
    r"""--build-arg\s+PYTHON_IMAGE=(["']?)\$\{(?:env\.)?PYTHON_IMAGE\}\1""")


def docker_build_commands(jenkinsfile: str) -> list[str]:
    """Return each ``docker build`` command of a Jenkinsfile on one line.

    The guard joins the lines that a trailing backslash continues.
    """
    commands: list[str] = []
    lines = jenkinsfile.splitlines()
    for index, line in enumerate(lines):
        if "docker build" not in line or is_comment(line):
            continue
        parts = [line.strip()]
        while parts[-1].endswith("\\") and index + 1 < len(lines):
            index += 1
            parts.append(lines[index].strip())
        commands.append(" ".join(part.rstrip("\\") for part in parts))
    return commands


def ci_builds_without_python_image_arg(jenkinsfile: str) -> list[str]:
    """Return the CI ``docker build`` commands that do not pass
    ``--build-arg PYTHON_IMAGE=${PYTHON_IMAGE}``."""
    found: list[str] = []
    for command in docker_build_commands(jenkinsfile):
        match = DOCKER_BUILD_FILE.search(command)
        if match is None or match.group(1) not in CI_DOCKERFILE_DIRS:
            continue
        if not PYTHON_IMAGE_BUILD_ARG.search(command):
            found.append(command)
    return found


def production_dockerfiles_built_with_the_arg(jenkinsfile: str) -> set[str]:
    """Return the production Dockerfiles that a ``docker build`` of the
    Jenkinsfile builds with ``--build-arg PYTHON_IMAGE=${PYTHON_IMAGE}``.
    """
    return {
        match.group(1)
        for command in docker_build_commands(jenkinsfile)
        if (match := DOCKER_BUILD_PRODUCTION_FILE.search(command))
        and PYTHON_IMAGE_BUILD_ARG.search(command)}


def read_or_skip(path: pathlib.Path) -> str:
    if not path.exists():
        pytest.skip(f"{path} is not in this tree; a checkout runs the check")
    return path.read_text()


def dockerfiles(root: pathlib.Path) -> dict[str, str]:
    """Map each Dockerfile under ``root`` to its text.

    The keys are paths relative to ``root``.
    """
    found: dict[str, str] = {}
    for top, dirs, files in os.walk(root):
        dirs[:] = [
            name for name in dirs
            if not name.startswith(".") and name not in SKIPPED_DIRS]
        for name in files:
            path = pathlib.Path(top) / name
            rel = path.relative_to(root).as_posix()
            if name.startswith("Dockerfile"):
                found[rel] = path.read_text()
    return found


def dockerfiles_or_skip() -> dict[str, str]:
    """Return the Dockerfiles of the tree, or skip.

    The check skips when a named Dockerfile is not in the tree, as in
    the ``core`` CI image.
    """
    found = dockerfiles(REPO_ROOT)
    missing = sorted(set(NAMED_DOCKERFILES) - found.keys())
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


def test_arg_without_a_default_is_reported() -> None:
    dockerfile = "ARG PYTHON_IMAGE\nFROM ${PYTHON_IMAGE}\n"

    assert arg_default_mismatches(dockerfile, "python:3.13-slim") == [
        "ARG PYTHON_IMAGE"]


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


def test_dockerfiles_include_the_production_dockerfiles(
    tmp_path: pathlib.Path,
) -> None:
    for rel in [*NAMED_PRODUCTION_DOCKERFILES, "core/Dockerfile"]:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("FROM python:3.12-slim\n")

    assert sorted(dockerfiles(tmp_path)) == sorted(
        [*NAMED_PRODUCTION_DOCKERFILES, "core/Dockerfile"])


def test_no_dockerfile_names_a_literal_python_image() -> None:
    found = {
        name: lines
        for name, text in dockerfiles_or_skip().items()
        if (lines := literal_python_from_lines(text))}

    assert found == {}


def test_dockerfile_defaults_match_the_jenkinsfile(
    ci_python_image: str,
) -> None:
    found = {
        name: lines
        for name, text in dockerfiles_or_skip().items()
        if (lines := arg_default_mismatches(text, ci_python_image))}

    assert found == {}


def test_named_dockerfiles_read_the_python_image_arg(
    ci_python_image: str,
) -> None:
    found = dockerfiles_or_skip()

    missing = [
        name for name in NAMED_DOCKERFILES
        if f"ARG PYTHON_IMAGE={ci_python_image}" not in found[name]
        or "FROM ${PYTHON_IMAGE}" not in found[name]]

    assert missing == []


def test_e2e_jenkinsfile_names_the_same_python_image(
    ci_python_image: str,
) -> None:
    e2e = jenkins_python_image(read_or_skip(E2E_JENKINSFILE))

    assert e2e == ci_python_image


def test_release_jenkinsfile_names_the_same_python_image(
    ci_python_image: str,
) -> None:
    release = read_or_skip(RELEASE_JENKINSFILE)

    assert literal_python_image_lines(release), \
        "the pip2pi container of Jenkinsfile.release names no python image"
    assert literal_python_image_mismatches(release, ci_python_image) == []


def test_release_pip2pi_image_that_differs_is_reported() -> None:
    release = (
        "    // the python:3.12-slim comment is skipped\n"
        "docker run --rm \\\\\n"
        "    -w /work \\\\\n"
        "    python:3.12-slim \\\\\n"
        "    sh -c 'pip install pip2pi && dir2pi .'\n")

    assert literal_python_image_mismatches(release, "python:3.13-slim") == [
        "python:3.12-slim \\\\"]


def test_release_pip2pi_image_that_matches_is_not_reported() -> None:
    release = (
        "docker run --rm \\\\\n"
        "    python:3.13-slim \\\\\n"
        "    sh -c 'pip install pip2pi && dir2pi .'\n")

    assert literal_python_image_mismatches(
        release, "python:3.13-slim") == []


def test_literal_python_container_in_a_jenkinsfile_is_reported() -> None:
    jenkinsfile = (
        "    PYTHON_IMAGE = 'python:3.13-slim'\n"
        "    // the python:3.12-slim comment is skipped\n"
        "    docker run --rm \\\n"
        "        python:3.12-slim \\\n"
        '        "${PYTHON_IMAGE}" \\\n')

    assert literal_python_image_lines(jenkinsfile) == [
        "python:3.12-slim \\"]


def test_ci_build_without_the_python_image_arg_is_reported() -> None:
    jenkinsfile = (
        "docker build -f core/Dockerfile \\\n"
        "    -t gpf-core-ci .\n"
        "docker build -f web_api/Dockerfile \\\n"
        "    --build-arg PYTHON_IMAGE=${PYTHON_IMAGE} \\\n"
        "    -t gpf-web-api-ci .\n"
        "docker build \\\n"
        "    -f web_api/Dockerfile.production \\\n"
        "    -t gpf-web-api .\n")

    assert ci_builds_without_python_image_arg(jenkinsfile) == [
        "docker build -f core/Dockerfile  -t gpf-core-ci ."]


def test_jenkinsfile_names_no_literal_python_image() -> None:
    lines = literal_python_image_lines(read_or_skip(JENKINSFILE))

    assert not lines, lines


def test_quoted_python_image_build_arg_is_accepted() -> None:
    jenkinsfile = (
        "docker build \\\n"
        "    -f web_api/Dockerfile.production \\\n"
        '    --build-arg PYTHON_IMAGE="${PYTHON_IMAGE}" \\\n'
        "    -t gpf-web-api .\n"
        "docker build \\\n"
        "    -f Dockerfile.production \\\n"
        "    --build-arg PYTHON_IMAGE=python:3.12-slim \\\n"
        "    -t gpf-web .\n")

    assert production_dockerfiles_built_with_the_arg(jenkinsfile) == {
        "web_api/Dockerfile.production"}


def test_jenkinsfile_builds_each_production_dockerfile_with_the_arg(
) -> None:
    found = production_dockerfiles_built_with_the_arg(
        read_or_skip(JENKINSFILE))

    assert found == set(NAMED_PRODUCTION_DOCKERFILES)


def test_e2e_jenkinsfile_names_no_literal_python_image() -> None:
    lines = literal_python_image_lines(read_or_skip(E2E_JENKINSFILE))

    assert not lines, lines


@pytest.mark.parametrize("path", [JENKINSFILE, E2E_JENKINSFILE])
def test_ci_builds_pass_the_python_image_arg(path: pathlib.Path) -> None:
    found = ci_builds_without_python_image_arg(read_or_skip(path))

    assert not found, found


def test_jenkinsfile_builds_each_ci_dockerfile_with_the_arg() -> None:
    commands = docker_build_commands(read_or_skip(JENKINSFILE))

    dirs = {
        match.group(1)
        for command in commands
        if (match := DOCKER_BUILD_FILE.search(command))
        and PYTHON_IMAGE_BUILD_ARG.search(command)}

    assert {"${name}", "web_api"} <= dirs


MATRIX_PY_AXIS = re.compile(
    r"name\s+'PY'\s+values\s+((?:'[^']*'\s*,?\s*)+)")
MATRIX_PYTHON_IMAGE_BUILD_ARG = re.compile(
    r"--build-arg\s+PYTHON_IMAGE=python:\\?\$\{PY\}-slim")


def matrix_python_versions(jenkinsfile: str) -> list[str]:
    """Return the values of the ``PY`` axis of the matrix Jenkinsfile."""
    match = MATRIX_PY_AXIS.search(jenkinsfile)
    if match is None:
        return []
    return re.findall(r"'([^']*)'", match.group(1))


def test_matrix_python_versions_reads_the_py_axis() -> None:
    jenkinsfile = (
        "axis {\n"
        "    name 'PY'\n"
        "    values '3.12', '3.13', '3.14'\n"
        "}\n"
        "axis {\n"
        "    name 'PROJECT'\n"
        "    values 'core', 'web_api'\n"
        "}\n")

    assert matrix_python_versions(jenkinsfile) == ["3.12", "3.13", "3.14"]


def read_matrix_jenkinsfile() -> str:
    """Read the matrix Jenkinsfile that the matrix Job DSL loads.

    The test skips when neither file is in the tree. The test fails when
    the Job DSL names the Jenkinsfile and the Jenkinsfile is missing.
    """
    if MATRIX_JOB_DSL.exists():
        assert MATRIX_JENKINSFILE.name in MATRIX_JOB_DSL.read_text()
        assert MATRIX_JENKINSFILE.exists(), (
            f"{MATRIX_JOB_DSL} loads {MATRIX_JENKINSFILE.name}, "
            "which is missing")
    return read_or_skip(MATRIX_JENKINSFILE)


def test_matrix_covers_the_default_interpreter(
    ci_python_image: str,
) -> None:
    matrix = read_matrix_jenkinsfile()
    version = ci_python_image.removeprefix("python:").removesuffix("-slim")

    assert version in matrix_python_versions(matrix)


def test_matrix_builds_each_cell_with_its_python_image() -> None:
    commands = docker_build_commands(read_matrix_jenkinsfile())

    assert commands
    assert all(
        MATRIX_PYTHON_IMAGE_BUILD_ARG.search(command)
        for command in commands), commands
