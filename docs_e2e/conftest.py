"""Session fixtures for docs_e2e/tests/.

Builds the system-under-test once per pytest run: install gpf_web
from the local conda channel, clone gpf-getting-started, import
the guide's demo data, configure the example dataset, then start
``wgpf run`` in a background subprocess and yield an httpx client.

Strict-mode contract (per #871 § Strict mode + #872):
the fixtures do nothing the guide itself doesn't tell the user
to do. The only invisible infrastructure here is the local
conda channel mount and the persistent GRR cache — both
transparent to the user's command path.

Run requirements (set by the docs-e2e Jenkinsfile, or by the
local-iteration command in docs_e2e/README.md):

* ``DOCS_E2E_CHANNEL`` — directory of ``gpf_web-*.conda`` files.
* ``DOCS_E2E_GRR_CACHE`` — directory persisted as the GRR cache.
"""

import os
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

# httpx is only needed inside the wgpf_server fixture. Importing
# lazily there keeps the guide_assertions unit-test suite (which
# runs as part of gpf-core CI in the regular .venv that does not
# ship httpx) from blowing up at conftest collection time. The
# docs-e2e driver image's `driver` mamba env installs httpx, so
# in-pipeline the fixture import is a no-op.


_INSTALL_TIMEOUT = 1800        # 30 min cap for the conda solve+install
_IMPORT_TIMEOUT = 1200         # 20 min per import_genotypes
_WGPF_READY_TIMEOUT = 180      # 3 min for wgpf to start serving
_WGPF_SHUTDOWN_TIMEOUT = 30


def _run(cmd, *, cwd=None, env=None, check=True, timeout=600):
    """subprocess.run wrapper that always captures and always
    returns the CompletedProcess (even on non-zero exit). When
    ``check=True``, raises only on the timeout or on genuine
    OSError — leaves return-code handling to the caller, who
    typically wants to feed the result into ``assert_command_succeeds``
    so the rich failure message comes through."""
    return subprocess.run(
        cmd, cwd=cwd, env=env, capture_output=True,
        check=False, timeout=timeout,
    )


@pytest.fixture(scope="session")
def conda_channel(tmp_path_factory):
    """Path to a freshly-indexed local conda channel built from the
    upstream gpf master archive's .conda artefacts.

    The upstream Jenkins copyArtifacts step leaves
    `DOCS_E2E_CHANNEL` as a *flat* directory of `.conda` files. A
    proper conda channel needs a `noarch/` (and/or `linux-64/`)
    subdirectory layout plus `repodata.json`. Without those, mamba
    fails with `Could not read a file:// file […]/noarch/repodata.json`.

    The fixture builds a session-scoped indexed channel in a tempdir:

      1. Hardlink (fall back to copy) every `.conda` into
         <tempdir>/noarch/ — the gpf packages all carry the `pyh*`
         build tag indicating noarch/python, so they live there.
      2. Run `python -m conda_index <tempdir>` to generate
         `<tempdir>/noarch/repodata.json`.

    Mamba then accepts `-c file://<tempdir>` and the install
    proceeds. Source remains untouched (often a bind-mounted RO
    workspace; tempdir keeps mutations local)."""
    src = Path(os.environ.get(
        "DOCS_E2E_CHANNEL", "/workspace/dist/conda",
    ))
    if not src.is_dir():
        pytest.fail(
            f"DOCS_E2E_CHANNEL={src} does not exist or is not a "
            f"directory. The Jenkinsfile copyArtifacts step should "
            f"populate dist/conda/; for local runs, point this at "
            f"a directory of gpf-web-*.conda files.",
            pytrace=False,
        )
    # The conda package name (per web_api/conda-recipe/recipe.yaml
    # `name: gpf-web`) uses a dash. The Python module name
    # `gpf_web` uses an underscore — conda normalizes between the
    # two so `mamba install gpf_web` resolves to the dash-named
    # package, but the on-disk artefact is always `gpf-web-*.conda`.
    if not any(src.glob("gpf-web-*.conda")):
        pytest.fail(
            f"No gpf-web-*.conda found in {src}. The freshly-built "
            f"conda artefact this suite is supposed to test is "
            f"missing.",
            pytrace=False,
        )

    channel = tmp_path_factory.mktemp("conda-channel", numbered=False)
    noarch = channel / "noarch"
    noarch.mkdir()
    for conda_file in src.glob("*.conda"):
        target = noarch / conda_file.name
        try:
            os.link(conda_file, target)
        except OSError:
            # Cross-filesystem or hardlink not permitted; fall back.
            shutil.copy2(conda_file, target)

    # Invoke conda_index via the BASE env's python — that env has
    # both `conda_index` (installed via the Dockerfile's
    # `mamba install -n base conda-index`) and the `conda` python
    # module conda_index depends on at runtime. The driver env's
    # python (which is the one running pytest right now) has
    # neither; the explicit absolute path is the cleanest cross-env
    # invocation.
    result = _run(
        ["/opt/conda/bin/python", "-m", "conda_index", str(channel)],
        timeout=300,
    )
    if result.returncode != 0:
        pytest.fail(
            "conda_index failed:\n"
            f"  stdout: {result.stdout.decode(errors='replace')[-2000:]}\n"
            f"  stderr: {result.stderr.decode(errors='replace')[-2000:]}",
            pytrace=False,
        )

    return channel


@pytest.fixture(scope="session")
def grr_cache_dir():
    """Persistent GRR cache mount. Per build, the same docker
    volume is mounted at the same in-container path, so demand-
    pulls of hg38 etc. are reused across builds on the same
    agent."""
    path = Path(os.environ.get(
        "DOCS_E2E_GRR_CACHE", "/grr-cache",
    ))
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def gpf_env_prefix(tmp_path_factory, conda_channel):
    """Create a fresh gpf-web conda env from the local channel +
    the upstream channels the guide tells users to add."""
    prefix = tmp_path_factory.mktemp("gpf-env-prefix", numbered=False)
    cmd = [
        "mamba", "create", "-y",
        "--prefix", str(prefix),
        "-c", f"file://{conda_channel}",
        "-c", "iossifovlab",
        "-c", "bioconda",
        "-c", "conda-forge",
        "gpf_web",
    ]
    result = _run(cmd, timeout=_INSTALL_TIMEOUT)
    if result.returncode != 0:
        pytest.fail(
            "mamba create gpf_web failed:\n"
            f"  stdout: {result.stdout.decode(errors='replace')[-4000:]}\n"
            f"  stderr: {result.stderr.decode(errors='replace')[-4000:]}",
            pytrace=False,
        )
    return prefix


@pytest.fixture(scope="session")
def gpf_env(gpf_env_prefix, grr_cache_dir):
    """Process env dict that puts the gpf-web env's bin/ first on
    PATH and points the GRR cache at the persistent volume."""
    env = os.environ.copy()
    env["PATH"] = f"{gpf_env_prefix}/bin:{env['PATH']}"
    env["CONDA_PREFIX"] = str(gpf_env_prefix)
    # GPF respects GRR_DEFINITION_FILE for an override. The
    # default-built-in GRR uses an OS cache path that's not the
    # persistent volume; pointing it at the mount keeps demand-
    # pulls hot across builds.
    env["GRR_CACHE_DIR"] = str(grr_cache_dir)
    return env


@pytest.fixture(scope="session")
def getting_started_clone(tmp_path_factory):
    """Shallow-clone iossifovlab/gpf-getting-started master.

    Uses the same source URL as docs/build_docs.sh — the build
    drives the guide against the same data the published guide
    refers to. No SHA pin (#871 § gpf-getting-started: clone master).
    """
    target = tmp_path_factory.mktemp("gpf-getting-started", numbered=False)
    # tmp_path_factory.mktemp creates the dir; git clone wants it
    # not to exist. Remove + clone.
    shutil.rmtree(target)
    result = _run([
        "git", "clone", "--depth", "1",
        "https://github.com/iossifovlab/gpf-getting-started.git",
        str(target),
    ])
    if result.returncode != 0:
        pytest.fail(
            "git clone gpf-getting-started failed:\n"
            f"  stderr: {result.stderr.decode(errors='replace')}",
            pytrace=False,
        )
    return target


@dataclass
class PreparedInstance:
    """Snapshot of the imported state of the GPF instance, plus
    the subprocess results of each setup step so per-test
    assertions can feed them into ``after_command=`` for triage."""

    clone_path: Path
    instance_dir: Path
    denovo_import: subprocess.CompletedProcess
    vcf_import: subprocess.CompletedProcess
    dataset_yaml_path: Path


@pytest.fixture(scope="session")
def prepared_instance(getting_started_clone, gpf_env):
    """Walk the guide's main body: setup → denovo import → vcf
    import → create example_dataset config.

    Captures each subprocess's result rather than raising on
    failure, so per-test assertions can produce rich messages
    via ``assert_command_succeeds`` / ``assert_file_created``.
    """
    clone = getting_started_clone
    instance_dir = clone / "minimal_instance"
    env = dict(gpf_env)
    # DAE_DB_DIR is what the guide's `export` line sets and what
    # wgpf/import_genotypes pick up.
    env["DAE_DB_DIR"] = str(instance_dir)

    denovo = _run(
        ["import_genotypes", "input_genotype_data/denovo_example.yaml"],
        cwd=clone, env=env, timeout=_IMPORT_TIMEOUT,
    )
    vcf = _run(
        ["import_genotypes", "input_genotype_data/vcf_example.yaml"],
        cwd=clone, env=env, timeout=_IMPORT_TIMEOUT,
    )

    # The guide tells the user to `mkdir -p datasets/example_dataset`
    # and write a small yaml. Mirror that exactly.
    dataset_dir = instance_dir / "datasets" / "example_dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    dataset_yaml = dataset_dir / "example_dataset.yaml"
    dataset_yaml.write_text(
        "id: example_dataset\n"
        "name: Example Dataset\n"
        "\n"
        "studies:\n"
        "  - denovo_example\n"
        "  - vcf_example\n"
    )

    return PreparedInstance(
        clone_path=clone,
        instance_dir=instance_dir,
        denovo_import=denovo,
        vcf_import=vcf,
        dataset_yaml_path=dataset_yaml,
    )


def _pick_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def wgpf_server(prepared_instance, gpf_env):
    """Start ``wgpf run`` in a background subprocess against the
    prepared instance; yield a SimpleNamespace with the base URL,
    httpx client, and the underlying Popen for log access.

    On teardown, terminates wgpf and dumps the last few hundred
    lines of its combined stdout/stderr if any test in the
    session failed."""
    import httpx  # lazy — see top-of-file note.

    env = dict(gpf_env)
    env["DAE_DB_DIR"] = str(prepared_instance.instance_dir)

    port = _pick_free_port()
    base_url = f"http://127.0.0.1:{port}"

    proc = subprocess.Popen(
        ["wgpf", "run", "--port", str(port), "--host", "127.0.0.1"],
        cwd=prepared_instance.instance_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    client = httpx.Client(base_url=base_url, timeout=60.0)

    # Poll for readiness. /api/v3/instance is a cheap, public
    # endpoint that exists once the Django app starts answering.
    deadline = time.monotonic() + _WGPF_READY_TIMEOUT
    last_err = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            out = proc.stdout.read().decode(errors="replace") if proc.stdout else ""
            pytest.fail(
                f"wgpf run exited early (returncode={proc.returncode}):\n"
                f"{out[-4000:]}",
                pytrace=False,
            )
        try:
            r = client.get("/api/v3/instance")
            if r.status_code < 500:
                break
            last_err = f"HTTP {r.status_code}"
        except httpx.RequestError as exc:
            last_err = repr(exc)
        time.sleep(1)
    else:
        # Readiness timeout. Capture log for the failure message.
        proc.terminate()
        try:
            proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        out = proc.stdout.read().decode(errors="replace") if proc.stdout else ""
        pytest.fail(
            f"wgpf run did not become ready within "
            f"{_WGPF_READY_TIMEOUT}s (last error: {last_err}):\n"
            f"{out[-4000:]}",
            pytrace=False,
        )

    try:
        yield SimpleNamespace(
            url=base_url, client=client, process=proc,
        )
    finally:
        client.close()
        proc.terminate()
        try:
            proc.communicate(timeout=_WGPF_SHUTDOWN_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
