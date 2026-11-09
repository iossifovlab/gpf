# pylint: disable=W0621,C0116
"""The mypy commands in the guides match the ``mypyTarget`` values in CI.

``CLAUDE.md`` and ``README.md`` show the mypy commands of the ``core``
and ``web_api`` stages. The ``Jenkinsfile`` passes the same targets to
``runProject(...)`` as ``mypyTarget``.
"""
import dataclasses
import pathlib
import re
import shlex
import textwrap

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]

CORE_PKG = "gpf"
WEB_API_PKG = "gpf_web"
JENKINSFILE = "Jenkinsfile"
GUIDES = ("CLAUDE.md", "README.md")


@dataclasses.dataclass(frozen=True)
class GuideMypyCommands:
    """The mypy commands of one guide."""

    web_api: list[frozenset[str]]
    core: list[tuple[str, ...]]


def _call_bodies(text: str, name: str) -> list[str]:
    """Return the argument text of each ``name(...)`` call.

    The scan skips quoted strings and drops ``//`` comments.
    """
    bodies = []
    for match in re.finditer(rf"\b{name}\(", text):
        depth = 1
        pos = match.end()
        body: list[str] = []
        while pos < len(text) and depth:
            char = text[pos]
            if char in "'\"":
                end = text.index(char, pos + 1)
                body.append(text[pos:end + 1])
                pos = end + 1
                continue
            if text.startswith("//", pos):
                pos = text.find("\n", pos)
                if pos == -1:
                    break
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            if depth:
                body.append(char)
            pos += 1
        bodies.append("".join(body))
    return bodies


def jenkinsfile_mypy_targets(text: str) -> dict[str, str]:
    """Return the ``mypyTarget`` of each ``runProject(...)``, keyed by pkg.

    Raise ``ValueError`` when the core or the web_api stage has no
    ``mypyTarget``.
    """
    targets = {}
    for body in _call_bodies(text, "runProject"):
        pkg = re.search(r"\bpkg:\s*'([^']*)'", body)
        target = re.search(
            r"\bmypyTarget:\s*('[^']*'(?:\s*\+\s*'[^']*')*)", body)
        if pkg and target:
            targets[pkg.group(1)] = "".join(
                re.findall(r"'([^']*)'", target.group(1)))
    for pkg_name in (CORE_PKG, WEB_API_PKG):
        if pkg_name not in targets:
            raise ValueError(
                f"the Jenkinsfile has no runProject(...) call with "
                f"pkg: '{pkg_name}' and a mypyTarget")
    return targets


def guide_mypy_commands(text: str) -> GuideMypyCommands:
    """Return the core and web_api mypy commands of a guide."""
    web_api: list[frozenset[str]] = []
    core: list[tuple[str, ...]] = []
    blocks = re.findall(
        r"^```bash\n(.*?)^```", text, re.MULTILINE | re.DOTALL)
    for block in blocks:
        for line in block.replace("\\\n", " ").splitlines():
            match = re.match(
                r"\s*cd (\S+) && uv run (?:--no-sync )?mypy\b(.*)", line)
            if not match:
                continue
            directory, args = match.group(1), shlex.split(match.group(2))
            if directory == "web_api" and "-p" in args:
                web_api.append(_packages(args))
            elif directory == "core":
                core.append(_positional(args))
    return GuideMypyCommands(web_api=web_api, core=core)


def _packages(args: list[str]) -> frozenset[str]:
    return frozenset(
        args[i + 1] for i, arg in enumerate(args[:-1]) if arg == "-p")


def _positional(args: list[str]) -> tuple[str, ...]:
    """Return the arguments of mypy that are not options."""
    result = []
    skip = False
    for arg in args:
        if skip:
            skip = False
        elif arg in {"--config-file", "-p"}:
            skip = True
        elif not arg.startswith("-"):
            result.append(arg)
    return tuple(result)


def guide_mismatches(
    guide_name: str, guide_text: str, targets: dict[str, str],
) -> list[str]:
    """Return one message for each mypy command that differs from CI."""
    commands = guide_mypy_commands(guide_text)
    expected_web_api = _packages(shlex.split(targets[WEB_API_PKG]))
    problems = []
    if not commands.web_api:
        problems.append(f"{guide_name}: no web_api mypy command found")
    if not commands.core:
        problems.append(f"{guide_name}: no core mypy command found")
    for packages in commands.web_api:
        missing = sorted(expected_web_api - packages)
        extra = sorted(packages - expected_web_api)
        if missing or extra:
            problems.append(
                f"{guide_name}: the web_api mypy -p set differs from the "
                f"Jenkinsfile mypyTarget of pkg '{WEB_API_PKG}'; "
                f"missing: {' '.join(missing) or '-'}; "
                f"extra: {' '.join(extra) or '-'}")
    expected_core = _positional(shlex.split(targets[CORE_PKG]))
    problems.extend(
        f"{guide_name}: the core mypy target "
        f"'{' '.join(target)}' differs from the Jenkinsfile "
        f"mypyTarget '{' '.join(expected_core)}' of pkg '{CORE_PKG}'"
        for target in commands.core
        if target != expected_core)
    return problems


def _read(root: pathlib.Path, name: str) -> str:
    path = root / name
    if not path.exists():
        pytest.fail(f"{path} is missing; the CI image must copy it")
    return path.read_text()


def repo_mypy_mismatches(root: pathlib.Path) -> list[str]:
    """Compare the guides under ``root`` with the Jenkinsfile there."""
    targets = jenkinsfile_mypy_targets(_read(root, JENKINSFILE))
    problems = []
    for guide_name in GUIDES:
        problems.extend(
            guide_mismatches(guide_name, _read(root, guide_name), targets))
    return problems


def _jenkinsfile(web_api_packages: list[str]) -> str:
    pieces = " +\n".join(f"        '-p {pkg} '" for pkg in web_api_packages)
    return textwrap.dedent("""\
        runProject(
            name: 'core',
            pkg: 'gpf',
            mypyTarget: 'gpf',
        )
        runProject(
            name: 'web_api',
            pkg: 'gpf_web',
            mypyTarget:
        {pieces},
        )
        """).format(pieces=pieces)


def _guide(web_api_packages: list[str], core_target: str = "gpf") -> str:
    flags = " ".join(f"-p {pkg}" for pkg in web_api_packages)
    return textwrap.dedent(f"""\
        ```bash
        cd core && uv run mypy {core_target}
        cd web_api && uv run mypy --config-file mypy.ini \\
            {flags}
        ```
        """)


def test_package_missing_from_guide_is_reported() -> None:
    jenkinsfile = _jenkinsfile(["gpf_web", "utils", "studies"])
    guide = _guide(["gpf_web", "utils"])

    problems = guide_mismatches(
        "GUIDE.md", guide, jenkinsfile_mypy_targets(jenkinsfile))

    assert len(problems) == 1
    assert "GUIDE.md" in problems[0]
    assert "missing: studies" in problems[0]


def test_package_extra_in_guide_is_reported() -> None:
    jenkinsfile = _jenkinsfile(["gpf_web", "utils"])
    guide = _guide(["gpf_web", "utils", "studies"])

    problems = guide_mismatches(
        "GUIDE.md", guide, jenkinsfile_mypy_targets(jenkinsfile))

    assert len(problems) == 1
    assert "GUIDE.md" in problems[0]
    assert "missing: -" in problems[0]
    assert "extra: studies" in problems[0]


def test_core_target_mismatch_is_reported() -> None:
    jenkinsfile = _jenkinsfile(["gpf_web", "utils"])
    guide = _guide(["gpf_web", "utils"], core_target="gpfx")

    problems = guide_mismatches(
        "GUIDE.md", guide, jenkinsfile_mypy_targets(jenkinsfile))

    assert len(problems) == 1
    assert "GUIDE.md" in problems[0]
    assert "core mypy target 'gpfx'" in problems[0]
    assert f"'{CORE_PKG}'" in problems[0]


def test_guide_without_web_api_command_is_reported() -> None:
    jenkinsfile = _jenkinsfile(["gpf_web", "utils"])
    guide = "```bash\ncd core && uv run mypy gpf\n```\n"

    problems = guide_mismatches(
        "GUIDE.md", guide, jenkinsfile_mypy_targets(jenkinsfile))

    assert problems == ["GUIDE.md: no web_api mypy command found"]


def test_guide_without_core_command_is_reported() -> None:
    jenkinsfile = _jenkinsfile(["gpf_web", "utils"])
    guide = (
        "```bash\n"
        "cd web_api && uv run mypy --config-file mypy.ini \\\n"
        "    -p gpf_web -p utils\n"
        "```\n")

    problems = guide_mismatches(
        "GUIDE.md", guide, jenkinsfile_mypy_targets(jenkinsfile))

    assert problems == ["GUIDE.md: no core mypy command found"]


def test_guide_parser_finds_no_sync_commands() -> None:
    guide = (
        "```bash\n"
        "cd core && uv run --no-sync mypy gpf\n"
        "cd web_api && uv run --no-sync mypy --config-file mypy.ini \\\n"
        "    -p gpf_web \\\n"
        "    -p utils\n"
        "```\n")

    commands = guide_mypy_commands(guide)

    assert commands == GuideMypyCommands(
        web_api=[frozenset({"gpf_web", "utils"})], core=[("gpf",)])


def test_jenkinsfile_without_web_api_stage_is_reported() -> None:
    jenkinsfile = "runProject(\n    pkg: 'gpf',\n    mypyTarget: 'gpf',\n)\n"

    with pytest.raises(ValueError, match="pkg: 'gpf_web'"):
        jenkinsfile_mypy_targets(jenkinsfile)


def test_missing_jenkinsfile_fails_the_file_check(
    tmp_path: pathlib.Path,
) -> None:
    for guide_name in GUIDES:
        (tmp_path / guide_name).write_text(_guide(["gpf_web", "utils"]))

    with pytest.raises(
        pytest.fail.Exception, match="the CI image must copy it",
    ) as excinfo:
        repo_mypy_mismatches(tmp_path)

    assert "Jenkinsfile" in str(excinfo.value)


def test_repo_guides_match_the_jenkinsfile() -> None:
    problems = repo_mypy_mismatches(REPO_ROOT)

    assert not problems, "\n".join(problems)
