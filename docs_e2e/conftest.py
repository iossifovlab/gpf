"""Session fixtures for docs_e2e/tests/.

Builds the system-under-test once per pytest run: install gpf-web
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

* ``DOCS_E2E_CHANNEL`` — directory of ``gpf-web-*.conda`` files.
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
# 10 min: the shared server now loads the 255K-variant ssc_denovo study
# alongside the example_dataset chain, so first-boot study/gene-model
# loading runs longer than the original 3 min budget. The ssc_denovo
# import (denovo_instance step 5) already applied the instance
# annotation, so a clean boot should NOT re-annotate.
_WGPF_READY_TIMEOUT = 600
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
    # The conda package is named `gpf-web` (dash) — per
    # web_api/conda-recipe/recipe.yaml. Both the `mamba install`
    # target and the on-disk artefact use the dash form; the guide
    # is kept in sync (it says `mamba install gpf-web`). The Python
    # *module* inside the package is still `gpf_web` (underscore),
    # but that name never appears on a conda command line.
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


# Sentinel file written into the persistent gpf-grr-cache volume by the
# gpf-docs-e2e-prewarm job, and ONLY after its grr_cache_repo run fully
# succeeds. The denovo guide's grr_cache_repo step
# (example_denovo_import.rst "Caching GRR") bulk-downloads ~15 GB of
# instance resources; that cost is paid OUT OF BAND by the prewarm job,
# never inside the wall-limited build. We key the guard on this sentinel
# rather than on the presence of a cached resource file: a partial
# demand-pull from an earlier build can leave a non-empty gnomAD file
# behind (which would false-pass a glob check) while the cache is still
# incomplete — exactly the case that made build #27's in-build
# grr_cache_repo time out. The sentinel only exists when a full cache
# write completed.
_SEED_SENTINEL = ".docs-e2e-prewarmed"


@pytest.fixture(scope="session")
def grr_cache_seeded(grr_cache_dir):
    """Fail fast if the agent's persistent GRR cache is not seeded.

    Gates the expensive fixtures (conda solve, imports) so an unseeded
    agent fails in seconds with an actionable message instead of letting
    grr_cache_repo cold-pull ~15 GB and blow the build timeout. Run the
    ``gpf-docs-e2e-prewarm`` job once per agent (see docs_e2e/README.md
    § Onboarding an agent)."""
    sentinel = grr_cache_dir / _SEED_SENTINEL
    if not sentinel.exists():
        node = os.environ.get("NODE_NAME", "<this-agent>")
        pytest.fail(
            f"GRR cache at {grr_cache_dir} is not seeded (sentinel "
            f"{_SEED_SENTINEL} absent). docs-e2e needs the ~15 GB "
            f"instance resources pre-cached on this agent. Run the "
            f"`gpf-docs-e2e-prewarm` Jenkins job against node '{node}' "
            f"once (it writes the sentinel on success), then re-trigger "
            f"this build. See docs_e2e/README.md § Onboarding an agent.",
            pytrace=False,
        )
    return grr_cache_dir


@pytest.fixture(scope="session")
def gpf_env_prefix(
    tmp_path_factory,
    conda_channel,
    grr_cache_seeded,  # noqa: ARG001 — ordering dep: cold-cache guard
):
    """Create a fresh gpf-web conda env from the local channel +
    the upstream channels the guide tells users to add.

    Depends on ``grr_cache_seeded`` purely for its side effect: an
    unseeded agent fails fast here, before this ~30 min conda solve,
    rather than after a 15 GB cold GRR pull deeper in the chain."""
    # mamba create --prefix refuses to write into a directory that
    # already exists as a non-conda folder ("Non-conda folder
    # exists at prefix"). tmp_path_factory.mktemp() *creates* the
    # dir, so point --prefix at a not-yet-existing subpath of it
    # and let mamba create the leaf.
    prefix = tmp_path_factory.mktemp("gpf-env", numbered=False) / "prefix"
    cmd = [
        "mamba", "create", "-y",
        "--prefix", str(prefix),
        "-c", f"file://{conda_channel}",
        "-c", "iossifovlab",
        "-c", "bioconda",
        "-c", "conda-forge",
        "gpf-web",
    ]
    result = _run(cmd, timeout=_INSTALL_TIMEOUT)
    if result.returncode != 0:
        pytest.fail(
            "mamba create gpf-web failed:\n"
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


# The gnomAD + ClinVar annotation block the annotation guide tells
# the user to append to gpf_instance.yaml — the emphasized lines
# 9-12 of the config code-block in
# getting_started_with_annotation.rst (RST lines 44-55). Kept
# byte-for-byte in sync with the guide; a drift here is itself a
# guide-accuracy bug the annotation suite is meant to catch.
_ANNOTATION_BLOCK = (
    "\n"
    "annotation:\n"
    "  config:\n"
    "    - allele_score: hg38/variant_frequencies/gnomAD_4.1.0/genomes/ALL\n"
    "    - allele_score: hg38/scores/ClinVar_20240730\n"
)


@dataclass
class AnnotatedInstance:
    """The instance after the annotation guide's config edit."""

    instance_dir: Path
    config_path: Path


@pytest.fixture(scope="session")
def annotated_instance(prepared_instance):
    """Apply getting_started_with_annotation.rst: append the gnomAD +
    ClinVar annotation block to minimal_instance/gpf_instance.yaml.

    Mirrors exactly the edit the guide tells the user to make. The
    re-annotation itself is NOT run here — per the guide it is
    triggered by ``wgpf run`` ("When you start the GPF instance using
    the wgpf tool, it will automatically re-annotate any genotype data
    that is not up to date"). The shared ``wgpf_server`` fixture
    depends on this fixture, so the single server starts against the
    annotated config and re-annotates on startup.

    Strict mode: the only thing done here is the yaml edit a real user
    types. No hidden re-annotation CLI, no pre-warming.
    """
    config_path = prepared_instance.instance_dir / "gpf_instance.yaml"
    config_path.write_text(config_path.read_text() + _ANNOTATION_BLOCK)
    return AnnotatedInstance(
        instance_dir=prepared_instance.instance_dir,
        config_path=config_path,
    )


# The line getting_started_with_phenotype_data.rst (RST line 112) tells
# the user to add to the example_dataset config to attach the imported
# pheno study. Kept byte-for-byte in sync with the guide.
_PHENOTYPE_DATA_LINE = "phenotype_data: mini_pheno\n"


@dataclass
class PhenotypeInstance:
    """The instance after the phenotype guide's import + dataset edit.

    Captures the ``import_phenotypes`` subprocess result so a per-test
    assertion can feed it into ``assert_command_succeeds`` for triage.
    """

    instance_dir: Path
    pheno_import: subprocess.CompletedProcess
    dataset_yaml_path: Path


@pytest.fixture(scope="session")
def phenotype_instance(annotated_instance, getting_started_clone, gpf_env):
    """Apply getting_started_with_phenotype_data.rst:

    1. ``import_phenotypes input_phenotype_data/import_project.yaml`` —
       imports the ``mini_pheno`` study into the instance's (default)
       phenotype storage.
    2. Append ``phenotype_data: mini_pheno`` to the example_dataset
       config — attaches the pheno study so the genotype dataset gains
       the Phenotype Browser / Phenotype Tool tabs + Pheno Measures
       filters.

    Both are exactly what the guide tells the user to type — a CLI
    import and a one-line yaml edit. ``wgpf_server`` depends on this
    fixture, so the single shared server serves the pheno-enabled
    instance. Chained after ``annotated_instance`` to keep the suite's
    linear-narrative ordering (imports → annotation edit → pheno).

    Strict mode (#871): no hidden phenotype-storage config, no silent
    migrate — the minimal_instance has no ``phenotype_storage:`` block
    and ``import_phenotypes`` falls back to a default storage on its
    own, which is the behaviour the guide relies on.
    """
    clone = getting_started_clone
    instance_dir = annotated_instance.instance_dir
    env = dict(gpf_env)
    env["DAE_DB_DIR"] = str(instance_dir)

    pheno_import = _run(
        ["import_phenotypes", "input_phenotype_data/import_project.yaml"],
        cwd=clone, env=env, timeout=_IMPORT_TIMEOUT,
    )

    dataset_yaml = (
        instance_dir / "datasets" / "example_dataset" / "example_dataset.yaml"
    )
    dataset_yaml.write_text(dataset_yaml.read_text() + _PHENOTYPE_DATA_LINE)

    return PhenotypeInstance(
        instance_dir=instance_dir,
        pheno_import=pheno_import,
        dataset_yaml_path=dataset_yaml,
    )


# The genotype_browser config getting_started_with_preview_columns.rst
# tells the user to add to the example_dataset config (the guide's second,
# final code-block — RST lines 127-161): the phenotype IQ columns, the
# redefined `frequency` group (now carrying gnomAD), the new `clinvar` and
# `proband_iq` column groups, and the preview_columns_ext that surfaces the
# two new groups in the preview table. Kept byte-for-byte in sync with the
# guide; a drift here is itself the guide-accuracy bug this suite catches.
_PREVIEW_COLUMNS_BLOCK = (
    "\n"
    "genotype_browser:\n"
    "  columns:\n"
    "    phenotype:\n"
    "      prb_verbal_iq:\n"
    "        role: prb\n"
    "        name: Verbal IQ\n"
    "        source: iq.verbal_iq\n"
    "\n"
    "      prb_non_verbal_iq:\n"
    "        role: prb\n"
    "        name: Non-Verbal IQ\n"
    "        source: iq.non_verbal_iq\n"
    "\n"
    "  column_groups:\n"
    "    frequency:\n"
    "      name: frequency\n"
    "      columns:\n"
    "      - allele_freq\n"
    "      - gnomad_v4_genome_ALL_af\n"
    "\n"
    "    clinvar:\n"
    "      name: ClinVar\n"
    "      columns:\n"
    "      - CLNSIG\n"
    "      - CLNDN\n"
    "\n"
    "    proband_iq:\n"
    "      name: Proband IQ\n"
    "      columns:\n"
    "      - prb_verbal_iq\n"
    "      - prb_non_verbal_iq\n"
    "\n"
    "  preview_columns_ext:\n"
    "    - clinvar\n"
    "    - proband_iq\n"
)


@dataclass
class PreviewColumnsInstance:
    """The instance after the preview-columns guide's example_dataset edit."""

    instance_dir: Path
    dataset_yaml_path: Path


@pytest.fixture(scope="session")
def preview_columns_instance(phenotype_instance):
    """Apply getting_started_with_preview_columns.rst: append the
    genotype_browser column-group + phenotype-column config to the
    example_dataset config.

    The guide walks two edits (first the gnomAD/ClinVar column groups, then
    the phenotype IQ columns), each followed by a ``wgpf`` restart. With the
    suite's single-shared-server invariant we apply the guide's *final*
    config — the second code-block (RST lines 127-161), a strict superset
    that keeps the ClinVar + redefined-frequency groups and adds the
    ``proband_iq`` phenotype group — and boot once. Every claim from both
    edits holds in that end state.

    Strict mode (#871): the only thing done here is the yaml edit a real
    user types. The phenotype columns reference the ``iq.*`` measures of the
    ``mini_pheno`` study attached by ``phenotype_instance``; chaining after
    it keeps the linear-narrative ordering and ensures those measures
    resolve when the server builds the dataset description.
    """
    dataset_yaml = phenotype_instance.dataset_yaml_path
    dataset_yaml.write_text(dataset_yaml.read_text() + _PREVIEW_COLUMNS_BLOCK)
    return PreviewColumnsInstance(
        instance_dir=phenotype_instance.instance_dir,
        dataset_yaml_path=dataset_yaml,
    )


# The awk pipeline example_denovo_import.rst (RST lines 111-124) tells
# the user to run to build ssc_denovo.ped from Supplementary_Data_1.tsv.gz.
# Reproduced byte-for-byte from the guide; a drift here is itself a
# guide-accuracy bug this suite is meant to catch.
_DENOVO_PED_AWK = r"""gunzip -c Supplementary_Data_1.tsv.gz | awk '
    BEGIN {
        OFS="\t"
        print "familyId", "personId", "dadId", "momId", "status", "sex"
    }
    $1 == "SSC" {
        fid = $2
        if( fid in families == 0) {
            families[fid] = 1
            print fid, fid".mo", "0", "0", "unaffected", "F"
            print fid, fid".fa", "0", "0", "unaffected", "M"
        }
        print fid, $3, fid".fa", fid".mo", $4, $5
    }' > ssc_denovo.ped"""


# The awk pipeline example_denovo_import.rst (RST lines 170-178) tells
# the user to run to build ssc_denovo.tsv from Supplementary_Data_2.tsv.gz.
# Reproduced byte-for-byte from the guide.
_DENOVO_TSV_AWK = r"""gunzip -c Supplementary_Data_2.tsv.gz | cut -f 4,9 | awk '
    BEGIN{
        OFS="\t"
        print "chrom", "pos", "ref", "alt", "person_id"
    }
    NR > 1 {
        split($2, v, ":")
        print v[1], v[2], v[3], v[4], $1
    }' > ssc_denovo.tsv"""


# The genotype_browser config block example_denovo_import.rst (RST lines
# 340-356) tells the user to append to the ssc_denovo study config: a
# `frequency` column group (allele_freq + gnomAD), a `clinvar` group
# (CLNSIG + CLNDN), and preview_columns_ext surfacing clinvar in the
# preview table. Kept byte-for-byte in sync with the guide.
_DENOVO_COLUMNS_BLOCK = (
    "\n"
    "genotype_browser:\n"
    "  column_groups:\n"
    "    frequency:\n"
    "      name: frequency\n"
    "      columns:\n"
    "      - allele_freq\n"
    "      - gnomad_v4_genome_ALL_af\n"
    "\n"
    "    clinvar:\n"
    "      name: ClinVar\n"
    "      columns:\n"
    "      - CLNSIG\n"
    "      - CLNDN\n"
    "\n"
    "  preview_columns_ext:\n"
    "    - clinvar\n"
)


# example_denovo_import.rst imports the ssc_denovo study and annotates it
# against the instance's gnomAD + ClinVar pipeline. Two things keep this fast
# and bounded under the build's 2400 s pytest-timeout:
#
#   1. The guide's grr_cache_repo step (run in denovo_instance below) caches
#      the instance resources into the persistent gpf-grr-cache volume. That
#      ~15 GB bulk download is paid OUT OF BAND by the gpf-docs-e2e-prewarm
#      job (the grr_cache_seeded guard asserts it is already present), so the
#      in-build call is a warm no-op validation — hence _GRR_CACHE_TIMEOUT.
#
#   2. STRICT-MODE EXCEPTION (#876): docs-e2e guards command accuracy, not
#      255K-scale import. denovo_instance truncates the awk-produced
#      ssc_denovo.tsv to the guide's first _DENOVO_VARIANT_CAP variants (all
#      chr1) before import. import_genotypes still runs verbatim; only the row
#      count differs, so the import completes in seconds against the warm
#      cache. A 90 min cap would be meaningless under the pytest-timeout.
_DENOVO_IMPORT_TIMEOUT = 600   # 10 min: warm cache + variant cap
_GRR_CACHE_TIMEOUT = 600       # 10 min: warm-cache validation (prewarmed)
_DENOVO_VARIANT_CAP = 50       # #876 carve-out — see note above


@dataclass
class DenovoInstance:
    """The instance after example_denovo_import.rst: ssc_denovo imported
    into minimal_instance and its study config edited with the
    frequency/ClinVar preview column groups.

    Captures each setup step's subprocess result so per-test assertions
    can feed them into ``after_command=`` / ``assert_command_succeeds``
    for triage.
    """

    instance_dir: Path
    clone_path: Path
    ped_awk: subprocess.CompletedProcess
    tsv_awk: subprocess.CompletedProcess
    grr_cache: subprocess.CompletedProcess
    ssc_denovo_import: subprocess.CompletedProcess
    study_config_path: Path


@pytest.fixture(scope="session")
def denovo_instance(
        preview_columns_instance, getting_started_clone, gpf_env,
        grr_cache_dir,
):
    """Apply example_denovo_import.rst: import the large ``ssc_denovo``
    study (255K real SSC de novo variants) into the same
    ``minimal_instance``, then edit the study config to add preview
    columns.

    Walks the guide's command path verbatim:

    1. The Family-Data awk (RST lines 111-124): reads
       ``Supplementary_Data_1.tsv.gz`` and writes ``ssc_denovo.ped``.
    2. The variant awk (RST lines 170-178): reads
       ``Supplementary_Data_2.tsv.gz`` and writes ``ssc_denovo.tsv``.
    3. Writes ``~/.grr_definition.yaml`` (the guide's "Caching GRR" step)
       pointing the GRR cache at the persistent ``grr_cache_dir`` volume,
       then runs ``grr_cache_repo -i minimal_instance/gpf_instance.yaml`` to
       cache the instance's annotation resources. ``grr_cache_repo`` ships in
       gain-core, a transitive dependency of the ``gpf-web`` conda package,
       so it is on PATH after the guide's ``mamba install gpf-web`` (no
       separate install step). Against the prewarmed persistent volume this
       is a fast validation; the ~15 GB cold download is paid out of band by
       the ``gpf-docs-e2e-prewarm`` job, asserted present by the
       ``grr_cache_seeded`` guard (see #876).
    4. ``import_genotypes -v -j 10 .../ssc_denovo.yaml`` (RST line 279):
       imports + annotates the study using the instance annotation.
    5. Appends the genotype_browser column-group block (RST lines 340-356)
       to the produced study config.

    Chained after ``preview_columns_instance`` to keep the suite's single
    ``wgpf run`` ordering: this is the last config edit the guide
    describes, so the single shared server (which depends on this fixture)
    boots against the fully-prepared instance.

    Strict mode (#871): every step here is a CLI command or file edit the
    guide tells the user to type. The only carve-out is the
    ``_DENOVO_VARIANT_CAP`` truncation of the awk output (#876) — see the
    constant's note; ``import_genotypes`` itself still runs verbatim.
    """
    clone = getting_started_clone
    instance_dir = preview_columns_instance.instance_dir
    import_dir = clone / "example_imports" / "denovo_and_cnv_import"
    env = dict(gpf_env)
    env["DAE_DB_DIR"] = str(instance_dir)

    # Steps 1-2: the two awk pipelines, run from the import dir.
    ped_awk = _run(
        ["bash", "-c", _DENOVO_PED_AWK],
        cwd=import_dir, env=env,
    )
    tsv_awk = _run(
        ["bash", "-c", _DENOVO_TSV_AWK],
        cwd=import_dir, env=env,
    )

    # STRICT-MODE EXCEPTION (#876): cap the awk output to the guide's first
    # _DENOVO_VARIANT_CAP variants (all chr1) so import_genotypes — still run
    # verbatim below — completes in seconds against the warm cache. docs-e2e
    # guards command accuracy, not 255K-scale import; only the row count
    # differs. test_example_denovo asserts the awk command's success and that
    # it produced ssc_denovo.tsv *before* this truncation mutates the file,
    # so the awk claims stay honestly tested.
    tsv_path = import_dir / "ssc_denovo.tsv"
    if tsv_awk.returncode == 0 and tsv_path.exists():
        rows = tsv_path.read_text().splitlines()
        tsv_path.write_text(
            "\n".join(rows[:_DENOVO_VARIANT_CAP + 1]) + "\n",
        )

    # Step 3: the guide's "Caching GRR" step — write ~/.grr_definition.yaml
    # pointing at the persistent cache volume, then run grr_cache_repo to
    # cache the instance's annotation resources. The grr_cache_seeded guard
    # already asserted the agent's persistent volume holds these (~15 GB,
    # pre-pulled out of band by gpf-docs-e2e-prewarm), so this is a warm
    # validation, not the cold download.
    grr_definition = Path.home() / ".grr_definition.yaml"
    grr_definition.write_text(
        'id: "seqpipe"\n'
        'type: "url"\n'
        'url: "https://grr.iossifovlab.com"\n'
        f'cache_dir: "{grr_cache_dir}"\n',
    )
    grr_cache = _run(
        [
            "grr_cache_repo", "-i",
            "minimal_instance/gpf_instance.yaml",
        ],
        cwd=clone, env=env, timeout=_GRR_CACHE_TIMEOUT,
    )

    # Step 4: import + annotate the (capped) study.
    ssc_denovo_import = _run(
        [
            "import_genotypes", "-v", "-j", "10",
            "example_imports/denovo_and_cnv_import/ssc_denovo.yaml",
        ],
        cwd=clone, env=env, timeout=_DENOVO_IMPORT_TIMEOUT,
    )

    # Step 5: append the genotype_browser column-group block to the study
    # config the import produced. The study id is `ssc_denovo`, so the
    # config lands under studies/<id>/<id>.yaml.
    study_config = (
        instance_dir / "studies" / "ssc_denovo" / "ssc_denovo.yaml"
    )
    if study_config.exists():
        study_config.write_text(
            study_config.read_text() + _DENOVO_COLUMNS_BLOCK)

    return DenovoInstance(
        instance_dir=instance_dir,
        clone_path=clone,
        ped_awk=ped_awk,
        tsv_awk=tsv_awk,
        grr_cache=grr_cache,
        ssc_denovo_import=ssc_denovo_import,
        study_config_path=study_config,
    )


# The awk pipeline example_cnv_import.rst (RST lines 76-83) tells the user
# to run to build ssc_cnv.tsv from Supplementary_Data_4.tsv.gz, keeping
# only the SSC-collection rows. Reproduced byte-for-byte from the guide;
# a drift here is itself a guide-accuracy bug this suite is meant to catch.
_CNV_AWK = r"""gunzip -c Supplementary_Data_4.tsv.gz | cut -f 2,5-7 | awk '
    BEGIN{
        OFS="\t"
        print "location", "variant", "person_id"
    }
    $1 == "SSC" {
        print $3, $4, $2
    }' > ssc_cnv.tsv"""

# example_cnv_import.rst imports the ssc_cnv study. STRICT-MODE EXCEPTION
# (#877, mirroring the #876 denovo cap): docs-e2e guards command accuracy,
# not full-scale import, so cnv_instance truncates the awk-produced
# ssc_cnv.tsv to the guide's first _CNV_VARIANT_CAP variants (all chr1)
# before import. import_genotypes still runs verbatim; only the row count
# differs, and the warm GRR cache keeps the annotation fast.
_CNV_VARIANT_CAP = 20


@dataclass
class CnvInstance:
    """The instance after example_cnv_import.rst: ssc_cnv imported into
    minimal_instance.

    Captures each setup step's subprocess result so per-test assertions
    can feed them into ``after_command=`` / ``assert_command_succeeds``
    for triage.
    """

    instance_dir: Path
    clone_path: Path
    cnv_awk: subprocess.CompletedProcess
    ssc_cnv_import: subprocess.CompletedProcess
    study_config_path: Path


@pytest.fixture(scope="session")
def cnv_instance(denovo_instance, getting_started_clone, gpf_env):
    """Apply example_cnv_import.rst: import the ``ssc_cnv`` study (SSC CNV
    variants) into the same ``minimal_instance``.

    Walks the guide's command path verbatim:

    1. The SSC-filter awk (RST lines 76-83): reads
       ``Supplementary_Data_4.tsv.gz`` and writes ``ssc_cnv.tsv``. The
       pedigree ``ssc_denovo.ped`` is reused from the denovo guide
       (created by ``denovo_instance``'s ped awk) — exactly as the guide
       says ("we already discussed how to transform the list of children
       into a pedigree file").
    2. ``import_genotypes -v -j 1 .../ssc_cnv.yaml`` (RST line 125):
       imports + annotates the CNV study using the instance annotation.

    Chained after ``denovo_instance`` to keep the suite's single ``wgpf
    run`` ordering: ``wgpf_server`` depends on this fixture, so the shared
    server boots with ``ssc_cnv`` added alongside everything else.

    Strict mode (#871): every step here is a CLI command the guide tells
    the user to type. The only carve-out is the ``_CNV_VARIANT_CAP``
    truncation of the awk output (#877) — see the constant's note;
    ``import_genotypes`` itself still runs verbatim.
    """
    clone = getting_started_clone
    instance_dir = denovo_instance.instance_dir
    import_dir = clone / "example_imports" / "denovo_and_cnv_import"
    env = dict(gpf_env)
    env["DAE_DB_DIR"] = str(instance_dir)

    # Step 1: the SSC-filter awk, run from the import dir.
    cnv_awk = _run(["bash", "-c", _CNV_AWK], cwd=import_dir, env=env)

    # STRICT-MODE EXCEPTION (#877): cap the awk output to the guide's first
    # _CNV_VARIANT_CAP SSC variants (all chr1) before import_genotypes —
    # which still runs verbatim below. Mirrors the #876 denovo cap. The awk
    # command's success and output file are asserted by test_example_cnv
    # before this truncation mutates the file.
    cnv_path = import_dir / "ssc_cnv.tsv"
    if cnv_awk.returncode == 0 and cnv_path.exists():
        rows = cnv_path.read_text().splitlines()
        cnv_path.write_text(
            "\n".join(rows[:_CNV_VARIANT_CAP + 1]) + "\n",
        )

    # Step 2: import + annotate the (capped) CNV study.
    ssc_cnv_import = _run(
        [
            "import_genotypes", "-v", "-j", "1",
            "example_imports/denovo_and_cnv_import/ssc_cnv.yaml",
        ],
        cwd=clone, env=env, timeout=_IMPORT_TIMEOUT,
    )

    # The study id is `ssc_cnv`, so the config lands under
    # studies/<id>/<id>.yaml. The CNV guide makes no further config edit.
    study_config = (
        instance_dir / "studies" / "ssc_cnv" / "ssc_cnv.yaml"
    )

    return CnvInstance(
        instance_dir=instance_dir,
        clone_path=clone,
        cnv_awk=cnv_awk,
        ssc_cnv_import=ssc_cnv_import,
        study_config_path=study_config,
    )


def _pick_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def wgpf_server(cnv_instance, gpf_env):
    """Start ``wgpf run`` in a background subprocess against the
    prepared instance; yield a SimpleNamespace with the base URL,
    httpx client, and the underlying Popen for log access.

    Depends on ``cnv_instance`` — the last stage of the guide's linear
    narrative (imports → annotation edit → pheno import + pheno attach →
    preview-column config → ssc_denovo import + study-column config →
    ssc_cnv import). ``cnv_instance`` transitively pulls the whole prior
    chain, so the single shared server starts after every config edit the
    guide describes: it serves the annotated, pheno-enabled example_dataset
    with its extended preview columns, the ssc_denovo study, AND the
    ssc_cnv study. Keeping the suite to one wgpf process per session avoids
    two ``wgpf run``s racing on the same ``DAE_DB_DIR`` parquet during
    re-annotation. Every earlier claim (datasets visible, annotation
    download columns, pheno browser) holds equally in this final state, so
    sharing one server across all stages is sound.

    On teardown, terminates wgpf and dumps the last few hundred
    lines of its combined stdout/stderr if any test in the
    session failed."""
    import httpx  # lazy — see top-of-file note.

    env = dict(gpf_env)
    env["DAE_DB_DIR"] = str(cnv_instance.instance_dir)

    port = _pick_free_port()
    base_url = f"http://127.0.0.1:{port}"

    proc = subprocess.Popen(
        ["wgpf", "run", "--port", str(port), "--host", "127.0.0.1"],
        cwd=denovo_instance.instance_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    client = httpx.Client(base_url=base_url, timeout=60.0)

    # Poll for readiness against /api/v3/datasets/ — the same
    # endpoint the production compose healthcheck uses
    # (web_infra/compose-jenkins-split.yaml). It returns 200 only
    # once WGPFInstance.studies_db is fully populated, i.e. after
    # the instance has finished building (loading reference genome
    # + gene models from the GRR, which takes several seconds).
    #
    # Earlier this polled /api/v3/instance and accepted any
    # status < 500 — but /api/v3/instance is NOT a route (it 404s),
    # and 404 < 500 made the fixture report "ready" the instant
    # Django started answering, long before studies loaded. Tests
    # then saw an empty /datasets/visible. Require == 200 on
    # /datasets/ so we wait for the instance, not just for Django.
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
            r = client.get("/api/v3/datasets/")
            if r.status_code == 200:
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
