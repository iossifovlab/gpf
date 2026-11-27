# pylint: disable=W0621,C0116
"""``scripts/gain_core_pin_freshness.sh`` warns about an old gain pin.

The `Pre-flight: tag freshness` stage of ``Jenkinsfile.release`` runs the
script when the operator sets ``GAIN_PIN_VERSION``. A stub ``curl`` first
on ``PATH`` answers the anaconda.org package URL with a fixed JSON body,
so the tests never reach the network.
"""
import os
import pathlib
import stat
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "gain_core_pin_freshness.sh"

PACKAGE_URL = "https://api.anaconda.org/package/iossifovlab/gain-core"

# The stub prints the anaconda.org package document with the
# `latest_version` that the test gives. A `latest` of None stands for
# a network failure: curl then prints an error and exits non-zero.
STUB_CURL = """#!/usr/bin/env bash
for url in "$@"; do :; done
if [ "$url" != "{package_url}" ]; then
    echo "stub curl: unexpected URL $url" >&2
    exit 99
fi
if [ "{latest}" = "None" ]; then
    echo "curl: (6) Could not resolve host" >&2
    exit 6
fi
printf '%s' '{{"name": "gain-core", "latest_version": "{latest}", \
"versions": ["2026.9.0", "{latest}"]}}'
"""


def run_check(
    tmp_path: pathlib.Path,
    *,
    pin: str,
    latest: str | None,
) -> subprocess.CompletedProcess[str]:
    if not SCRIPT.exists():
        pytest.fail(f"{SCRIPT} is missing; the CI image must copy it")
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    stub = stub_dir / "curl"
    stub.write_text(STUB_CURL.format(
        package_url=PACKAGE_URL,
        latest=latest,
    ))
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    env = {
        **os.environ,
        "PATH": f"{stub_dir}{os.pathsep}{os.environ['PATH']}",
        "GAIN_PIN_VERSION": pin,
    }
    return subprocess.run(
        ["bash", str(SCRIPT)],  # ruff: ignore[start-process-with-partial-path]
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_older_pin_warns_with_both_versions(tmp_path: pathlib.Path) -> None:
    result = run_check(tmp_path, pin="2026.11.0", latest="2026.11.1")

    assert result.returncode == 0, result.stderr
    assert (
        "WARNING: GAIN_PIN_VERSION 2026.11.0 is older than the newest "
        "gain-core 2026.11.1 on iossifovlab"
        in result.stdout
    )


def test_older_month_field_warns(tmp_path: pathlib.Path) -> None:
    result = run_check(tmp_path, pin="2026.9.0", latest="2026.10.0")

    assert result.returncode == 0, result.stderr
    assert (
        "WARNING: GAIN_PIN_VERSION 2026.9.0 is older than the newest "
        "gain-core 2026.10.0 on iossifovlab"
        in result.stdout
    )


@pytest.mark.parametrize("pin", ["2026.11.1", "2026.12.0"])
def test_equal_or_newer_pin_prints_info(
    tmp_path: pathlib.Path, pin: str,
) -> None:
    result = run_check(tmp_path, pin=pin, latest="2026.11.1")

    assert result.returncode == 0, result.stderr
    assert (
        f"Gain pin freshness: GAIN_PIN_VERSION {pin} is not older than "
        "the newest gain-core 2026.11.1 on iossifovlab"
        in result.stdout
    )
    assert "WARNING" not in result.stdout + result.stderr


def test_empty_pin_skips_without_warning(tmp_path: pathlib.Path) -> None:
    result = run_check(tmp_path, pin="", latest="2026.11.1")

    assert result.returncode == 0, result.stderr
    assert "WARNING" not in result.stdout + result.stderr
    assert "GAIN_PIN_VERSION is not set" in result.stdout


def test_network_failure_warns_and_passes(tmp_path: pathlib.Path) -> None:
    result = run_check(tmp_path, pin="2026.11.0", latest=None)

    assert result.returncode == 0, result.stderr
    assert (
        "WARNING: cannot read the newest gain-core version from "
        f"{PACKAGE_URL}"
        in result.stdout
    )
    assert "is older than" not in result.stdout
