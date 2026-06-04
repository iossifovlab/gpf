"""Guide-claim tests for getting_started_with_python_interface.rst.

The python-interface sub-guide is the last of the Getting Started guides and
the only REST-free one: a Jupyter-notebook-style narrative that drives the GPF
Python API directly. It builds one ``GPFInstance`` from the startup instance
the earlier guides produced, then runs a sequence of query snippets — listing
studies, querying ``example_dataset`` variants, and reading ``mini_pheno``
phenotype instruments/measures — each annotated with the value it "will
produce".

docs-e2e runs those snippets faithfully in a single python process in the
gpf-web conda env (the ``python_interface_session`` fixture in conftest.py;
see its docstring) and captures a JSON summary of each one's result. Each test
here asserts one discrete documented claim against the captured value via
``assert_python_snippet_output`` (which carries the rst_ref + a triage hint on
failure). No ``wgpf run`` is involved — this is pure Python API.

Import-namespace drift (the headline bug this sub-guide catches): the GPF
Python package was renamed ``dae`` -> ``gpf``; the guide's ``import`` snippets
must use the current ``gpf.`` namespace. That is a static property of the RST
prose, not something the runtime driver re-derives (the driver hardcodes the
working import so it can run), so ``test_guide_uses_current_import_namespace``
guards it by reading the RST directly.

Each test maps to one discrete prose claim. ``rst_ref`` points at the line in
the guide source so a failure localizes the drift.
"""

from pathlib import Path

from docs_e2e.guide_assertions import (
    assert_command_succeeds,
    assert_python_snippet_output,
)

RST = "getting_started_with_python_interface.rst"

# The RST lives in the gpf docs tree (a path relative to this test file's repo
# root) — the same root conftest reads the gene_profiles.yaml literalinclude
# from. Used by the static import-namespace check.
_GPF_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_RST_PATH = (
    _GPF_REPO_ROOT
    / "docs/source/administration/getting_started" / RST
)

# RST line 29: the ids of all configured genotype studies, in the order-
# independent set the guide lists. Every study the earlier guides imported:
# the two demo studies (denovo_example, vcf_example), their example_dataset
# group, plus ssc_denovo + ssc_cnv.
_GENOTYPE_DATA_IDS = sorted([
    "ssc_denovo", "denovo_example", "vcf_example", "ssc_cnv", "example_dataset",
])

# RST lines 54-77: the alt alleles the guide prints for the full
# example_dataset query — str(family_allele) is
# "<chrom>:<pos> <ref>-><alt> <family_id>". Order-independent (the guide's
# iteration order is not a documented claim); the driver sorts, so does this.
_EXAMPLE_DATASET_ALT_ALLELES = sorted([
    "chr14:21385738 C->T f1",
    "chr14:21385738 C->T f2",
    "chr14:21385954 A->C f2",
    "chr14:21391016 A->AT f2",
    "chr14:21393173 T->C f1",
    "chr14:21393484 TCTTC->T f2",
    "chr14:21393540 GGAA->G f1",
    "chr14:21393702 C->T f2",
    "chr14:21393860 G->A f1",
    "chr14:21402010 G->A f1",
    "chr14:21403019 G->A f2",
    "chr14:21403023 G->A f1",
    "chr14:21403023 G->A f2",
    "chr14:21403214 T->C f1",
    "chr14:21405222 T->C f2",
    "chr14:21409849 A->G f1",
    "chr14:21409888 T->C f1",
    "chr14:21409888 T->C f2",
    "chr14:21429019 C->T f1",
    "chr14:21429019 C->T f2",
    "chr14:21431306 G->A f1",
    "chr14:21431459 G->C f1",
    "chr14:21431499 T->C f2",
    "chr14:21431623 A->C f2",
])

# RST line 90: synonymous variants in example_dataset.
_SYNONYMOUS_COUNT = 4
# RST line 103: synonymous variants in example_dataset, role prb only.
_SYNONYMOUS_PRB_COUNT = 1

# RST line 118: the ids of all configured phenotype data.
_PHENOTYPE_DATA_IDS = sorted(["ssc_pheno", "mini_pheno"])

# RST line 134: mini_pheno instruments and the number of measures in each
# ("Instrument(basic_medical, 4)" / "Instrument(iq, 3)").
_INSTRUMENTS = {"basic_medical": 4, "iq": 3}

# RST lines 143-149: the seven mini_pheno measure ids.
_MEASURES = sorted([
    "basic_medical.age",
    "basic_medical.weight",
    "basic_medical.height",
    "basic_medical.race",
    "iq.diagnosis-notes",
    "iq.verbal-iq",
    "iq.non-verbal-iq",
])

# RST lines 161-178: non-verbal IQ for the probands of f1, f2, f3.
_PEOPLE_MEASURE_VALUES = [
    {"person_id": "f1.p1", "iq.non-verbal-iq": 70},
    {"person_id": "f2.p1", "iq.non-verbal-iq": 45},
    {"person_id": "f3.p1", "iq.non-verbal-iq": 93},
]


class TestGpfInstance:
    """RST lines 4-14: build a ``GPFInstance`` from the startup instance."""

    def test_guide_uses_current_import_namespace(self):
        # RST lines 9 + 155: the guide imports from the GPF Python package.
        # The package was renamed `dae` -> `gpf`; a guide still importing
        # `from dae.…` is the canonical drift this sub-guide catches. Guard it
        # statically against the RST source — the runtime driver hardcodes the
        # working import so it cannot re-derive this.
        assert _RST_PATH.is_file(), (
            f'DRIFT at {RST}:1 — "the python-interface guide exists"\n\n'
            f"  expected guide file: {_RST_PATH}\n"
            f"  actual:              does not exist\n"
        )
        text = _RST_PATH.read_text()
        # The GPF Python package was renamed `dae` -> `gpf`; the guide must
        # not import from the old namespace, and must import GPFInstance from
        # its current module path. Drift here is the headline bug this
        # sub-guide catches.
        stale_dae = (
            f'DRIFT at {RST}:9 — "import GPFInstance from the gpf package"\n\n'
            f"  expected: imports use the current `gpf.` namespace\n"
            f"  actual:   the guide still imports from the `dae` package\n\n"
            f"  Triage hint: the GPF Python package was renamed `dae` -> "
            f"`gpf`. Update the guide's `from dae.` import lines to "
            f"`from gpf.`. This is guide drift, not a code regression."
        )
        assert "from dae." not in text, stale_dae
        assert "import dae" not in text, stale_dae
        expected_import = (
            "from gpf.gpf_instance.gpf_instance import GPFInstance"
        )
        assert expected_import in text, (
            f'DRIFT at {RST}:9 — "import GPFInstance from the gpf package"\n\n'
            f"  expected: {expected_import!r} present in the guide\n"
            f"  actual:   not found\n\n"
            f"  Triage hint: the guide's GPFInstance import drifted from the "
            f"current module path. If the module moved, update the guide."
        )

    def test_gpf_instance_builds(self, python_interface_session):
        # RST lines 7-10: GPFInstance.build() instantiates the interface. The
        # driver script's first action is exactly that; a non-zero exit means
        # the build (or an import) raised — assert_command_succeeds surfaces
        # the traceback.
        assert_command_succeeds(
            python_interface_session.process,
            rst_ref=f"{RST}:10",
            expectation=(
                "GPFInstance.build() instantiates the GPF Python interface"
            ),
        )


class TestQueryingGenotypeData:
    """RST lines 16-103: list studies and query example_dataset variants."""

    def test_get_genotype_data_ids(self, python_interface_session):
        # RST lines 21-29: get_genotype_data_ids() returns the ids of all
        # configured studies.
        assert_python_snippet_output(
            python_interface_session.values, "genotype_data_ids",
            _GENOTYPE_DATA_IDS,
            rst_ref=f"{RST}:29",
            expectation=(
                "get_genotype_data_ids() lists every configured study"
            ),
            after_command=python_interface_session.process,
        )

    def test_query_variants_all(self, python_interface_session):
        # RST lines 33-75: querying example_dataset and printing each alt
        # allele produces the documented list of variants.
        assert_python_snippet_output(
            python_interface_session.values, "example_dataset_alt_alleles",
            _EXAMPLE_DATASET_ALT_ALLELES,
            rst_ref=f"{RST}:54",
            expectation=(
                "query_variants() over example_dataset yields the documented "
                "alt alleles"
            ),
            after_command=python_interface_session.process,
        )

    def test_query_variants_synonymous(self, python_interface_session):
        # RST lines 81-90: filtering by effect_types=['synonymous'] yields 4
        # variants.
        assert_python_snippet_output(
            python_interface_session.values, "synonymous_count",
            _SYNONYMOUS_COUNT,
            rst_ref=f"{RST}:90",
            expectation=(
                "query_variants(effect_types=['synonymous']) yields 4 variants"
            ),
            after_command=python_interface_session.process,
        )

    def test_query_variants_synonymous_prb(self, python_interface_session):
        # RST lines 95-103: adding roles='prb' narrows the synonymous query to
        # 1 variant.
        assert_python_snippet_output(
            python_interface_session.values, "synonymous_prb_count",
            _SYNONYMOUS_PRB_COUNT,
            rst_ref=f"{RST}:103",
            expectation=(
                "query_variants(effect_types=['synonymous'], roles='prb') "
                "yields 1 variant"
            ),
            after_command=python_interface_session.process,
        )


class TestQueryingPhenotypeData:
    """RST lines 105-178: list phenotype data and read mini_pheno
    instruments, measures, and per-person measure values."""

    def test_get_phenotype_data_ids(self, python_interface_session):
        # RST lines 110-118: get_phenotype_data_ids() returns the ids of all
        # configured phenotype data.
        assert_python_snippet_output(
            python_interface_session.values, "phenotype_data_ids",
            _PHENOTYPE_DATA_IDS,
            rst_ref=f"{RST}:118",
            expectation=(
                "get_phenotype_data_ids() lists every configured phenotype "
                "study"
            ),
            after_command=python_interface_session.process,
        )

    def test_instruments(self, python_interface_session):
        # RST lines 124-134: mini_pheno exposes the basic_medical (4 measures)
        # and iq (3 measures) instruments.
        assert_python_snippet_output(
            python_interface_session.values, "instruments",
            _INSTRUMENTS,
            rst_ref=f"{RST}:134",
            expectation=(
                "mini_pheno exposes the basic_medical and iq instruments"
            ),
            after_command=python_interface_session.process,
        )

    def test_measures(self, python_interface_session):
        # RST lines 137-149: mini_pheno exposes the seven documented measures.
        assert_python_snippet_output(
            python_interface_session.values, "measures",
            _MEASURES,
            rst_ref=f"{RST}:149",
            expectation="mini_pheno exposes the seven documented measures",
            after_command=python_interface_session.process,
        )

    def test_people_measure_values(self, python_interface_session):
        # RST lines 153-178: non-verbal IQ for the probands of f1, f2, f3.
        assert_python_snippet_output(
            python_interface_session.values, "people_measure_values",
            _PEOPLE_MEASURE_VALUES,
            rst_ref=f"{RST}:178",
            expectation=(
                "get_people_measure_values() returns the probands' non-verbal "
                "IQ for f1, f2, f3"
            ),
            after_command=python_interface_session.process,
        )
