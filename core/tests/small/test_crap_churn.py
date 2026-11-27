# pylint: disable=W0621,C0116
"""The churn log of the CRAP hotspot table (#1187).

The "Prepare workspace" stage of the root ``Jenkinsfile`` writes the
``git log`` text that ``scripts/crap_report_html.py`` reads. These tests
pin the step and run the same ``git log`` options on a small repo.
"""
import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
from types import ModuleType

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "crap_report_html.py"
JENKINSFILE = REPO_ROOT / "Jenkinsfile"

# The options of the git log call of the Jenkinsfile step. The test of
# the step checks that the Jenkinsfile has the same text.
GIT_LOG_OPTIONS = "-M --name-status --since=12.months --format=@@commit:%H"
CHURN_LOG = "reports/core/crap_churn_log.txt"
GIT = shutil.which("git")


@pytest.fixture(scope="module")
def crap_report_html() -> ModuleType:
    if not SCRIPT.exists():
        pytest.fail(f"{SCRIPT} is missing; core/Dockerfile must copy it")
    spec = importlib.util.spec_from_file_location(
        "crap_report_html", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def jenkinsfile() -> str:
    # core/Dockerfile copies the Jenkinsfile, so the CI image runs these
    # tests. A missing Jenkinsfile is a broken copy, not a reason to skip.
    if not JENKINSFILE.exists():
        pytest.fail(
            f"{JENKINSFILE} is missing; core/Dockerfile must copy it")
    return JENKINSFILE.read_text()


def between(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin:text.index(end, begin + len(start))]


def crap_step(jenkinsfile: str) -> str:
    """The shell text of ``crapStep``, without its Groovy assignment."""
    opening = jenkinsfile.index('"""\n', jenkinsfile.index("String crapStep"))
    body = jenkinsfile[opening + len('"""\n'):]
    return body[:body.index('\n"""')]


def prepare_workspace(jenkinsfile: str) -> str:
    return between(
        jenkinsfile, "stage('Prepare workspace')", "stage('Detect change")


def test_options_end_with_the_commit_marker_of_the_parser(
    crap_report_html: ModuleType,
) -> None:
    assert GIT_LOG_OPTIONS.endswith(
        f"--format={crap_report_html.COMMIT_MARKER}%H")


def test_prepare_workspace_writes_the_churn_log(jenkinsfile: str) -> None:
    stage = prepare_workspace(jenkinsfile)

    assert f"git log {GIT_LOG_OPTIONS} >" in stage
    assert CHURN_LOG in stage


def test_failed_git_log_removes_the_partial_file(jenkinsfile: str) -> None:
    stage = prepare_workspace(jenkinsfile)
    step = stage[stage.index(f"git log {GIT_LOG_OPTIONS}"):]
    failure = step[step.index("else"):step.index("fi")]

    assert 'rm -f "$churn.tmp"' in failure


def test_crap_step_passes_the_churn_log_and_the_root(
    jenkinsfile: str,
) -> None:
    step = crap_step(jenkinsfile)
    # The report call is the last command of crapStep, so the cut ends at
    # the end of the text. #1189 adds the gate call after it.
    call = step[step.index("/workspace/scripts/crap_report_html.py"):]
    call = " ".join(call.replace("\\", " ").split())

    assert call == (
        "/workspace/scripts/crap_report_html.py /reports/crap.txt "
        "/reports/crap.html /reports/crap_churn_log.txt ${crapRoot}")


def test_crap_step_holds_no_apostrophe(jenkinsfile: str) -> None:
    assert "'" not in crap_step(jenkinsfile)


def git(repo: pathlib.Path, *args: str) -> str:
    """Run git in the repo with a fixed identity and no global config."""
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    result = subprocess.run(
        [GIT or "git", "-c", "user.name=Test",
         "-c", "user.email=test@example.com", "-C", str(repo), *args],
        env=env, check=True, capture_output=True, text=True)
    return result.stdout


def commit_file(repo: pathlib.Path, path: str, text: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"change {path}")


@pytest.mark.skipif(GIT is None, reason="git is not on PATH")
def test_parser_counts_across_a_rename_in_a_real_log(
    crap_report_html: ModuleType, tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    body = "".join(f"line {i}\n" for i in range(20))
    commit_file(repo, "gpf_core/gpf/a.py", body)
    commit_file(repo, "gpf_core/gpf/a.py", body + "edit 1\n")
    (repo / "core" / "gpf").mkdir(parents=True)
    git(repo, "mv", "gpf_core/gpf/a.py", "core/gpf/a.py")
    git(repo, "commit", "-q", "-m", "rename")
    commit_file(repo, "core/gpf/a.py", body + "edit 1\nedit 2\n")

    log = git(repo, "log", *GIT_LOG_OPTIONS.split())

    assert crap_report_html.parse_churn_log(log) == {"core/gpf/a.py": 3}
