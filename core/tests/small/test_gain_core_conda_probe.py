# pylint: disable=W0621,C0116
"""``scripts/gain_core_conda_probe.sh`` finds gain-core on a conda channel.

The `Pre-flight: tag freshness` stage of ``Jenkinsfile.release`` runs the
script when the operator sets ``GAIN_PIN_VERSION``. A stub ``curl`` first
on ``PATH`` answers each anaconda.org API URL with a fixed HTTP code, so
the tests never reach the network.
"""
import os
import pathlib
import stat
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "gain_core_conda_probe.sh"

VERSION = "2026.11.0"
BIOCONDA_URL = (
    f"https://api.anaconda.org/release/bioconda/gain-core/{VERSION}")
IOSSIFOVLAB_URL = (
    f"https://api.anaconda.org/release/iossifovlab/gain-core/{VERSION}")

# The stub prints the HTTP code that the test assigns to the URL, the
# way `curl -w '%{http_code}'` does. A code of 000 stands for a network
# failure: curl then prints 000 and exits non-zero.
STUB_CURL = """#!/usr/bin/env bash
for url in "$@"; do :; done
case "$url" in
    {bioconda_url}) code={bioconda_code} ;;
    {iossifovlab_url}) code={iossifovlab_code} ;;
    *) echo "stub curl: unexpected URL $url" >&2; exit 99 ;;
esac
printf '%s' "$code"
if [ "$code" = "000" ]; then
    echo "curl: (6) Could not resolve host" >&2
    exit 6
fi
"""


def run_probe(
    tmp_path: pathlib.Path,
    *,
    bioconda: str,
    iossifovlab: str,
    version: str = VERSION,
) -> subprocess.CompletedProcess[str]:
    if not SCRIPT.exists():
        pytest.fail(f"{SCRIPT} is missing; the CI image must copy it")
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    stub = stub_dir / "curl"
    stub.write_text(STUB_CURL.format(
        bioconda_url=BIOCONDA_URL,
        bioconda_code=bioconda,
        iossifovlab_url=IOSSIFOVLAB_URL,
        iossifovlab_code=iossifovlab,
    ))
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    env = {
        **os.environ,
        "PATH": f"{stub_dir}{os.pathsep}{os.environ['PATH']}",
        "GAIN_PIN_VERSION": version,
    }
    return subprocess.run(
        ["bash", str(SCRIPT)],  # ruff: ignore[start-process-with-partial-path]
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_present_on_bioconda_passes(tmp_path: pathlib.Path) -> None:
    result = run_probe(tmp_path, bioconda="200", iossifovlab="404")

    assert result.returncode == 0, result.stderr
    assert (
        f"Gain conda probe: gain-core {VERSION} present on bioconda"
        in result.stdout
    )


def test_present_on_both_channels_names_bioconda(
    tmp_path: pathlib.Path,
) -> None:
    result = run_probe(tmp_path, bioconda="200", iossifovlab="200")

    assert result.returncode == 0, result.stderr
    assert (
        f"Gain conda probe: gain-core {VERSION} present on bioconda"
        in result.stdout
    )
    assert "present on iossifovlab" not in result.stdout


def test_present_only_on_iossifovlab_passes(tmp_path: pathlib.Path) -> None:
    result = run_probe(tmp_path, bioconda="404", iossifovlab="200")

    assert result.returncode == 0, result.stderr
    assert (
        f"Gain conda probe: gain-core {VERSION} present on iossifovlab"
        in result.stdout
    )


def test_absent_on_both_channels_fails(tmp_path: pathlib.Path) -> None:
    result = run_probe(tmp_path, bioconda="404", iossifovlab="404")

    assert result.returncode == 1
    assert VERSION in result.stderr
    assert "bioconda" in result.stderr
    assert "iossifovlab" in result.stderr
    assert "lags a gain release" in result.stderr


def test_network_failure_on_both_channels_fails(
    tmp_path: pathlib.Path,
) -> None:
    result = run_probe(tmp_path, bioconda="000", iossifovlab="000")

    assert result.returncode == 1
    assert "Could not resolve host" in result.stderr
    assert VERSION in result.stderr


def test_empty_version_is_a_probe_failure(tmp_path: pathlib.Path) -> None:
    result = run_probe(tmp_path, bioconda="200", iossifovlab="200", version="")

    assert result.returncode == 2
    assert "GAIN_PIN_VERSION" in result.stderr
