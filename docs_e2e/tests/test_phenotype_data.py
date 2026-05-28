"""Guide-claim tests for getting_started_with_phenotype_data.rst.

The phenotype section tells the user to:

1. import a simulated phenotype study with ``import_phenotypes`` — the
   ``mini_pheno`` study (two instruments, ``basic_medical`` and ``iq``)
   imported into the instance's phenotype storage;
2. re-run ``wgpf run`` — ``mini_pheno`` then appears on the Home Page and
   its instruments/measures are browsable in the Phenotype Browser;
3. attach the pheno study to ``example_dataset`` by adding
   ``phenotype_data: mini_pheno`` to its config — the genotype dataset
   then gains the Phenotype Browser + Phenotype Tool tabs and the
   genotype-browser Pheno Measures family/person filters.

The import + config edit live in the session-scoped
``phenotype_instance`` fixture (conftest.py); ``wgpf_server`` depends on
it, so the single shared server reflects the pheno-enabled state. Strict
mode (#871): the fixture only does what the guide tells the user to do —
the CLI import and the one-line yaml edit.

Each test maps to one discrete prose claim. ``rst_ref`` points at the
line in the guide source so a failure localizes the drift.
"""

import pytest

from docs_e2e.guide_assertions import (
    assert_command_succeeds,
    assert_dataset_description_flag,
    assert_dataset_visible,
    assert_image_response_ok,
    assert_pheno_instruments_available,
    assert_pheno_measures_present,
)

RST = "getting_started_with_phenotype_data.rst"

# The two instruments import_project.yaml imports (RST lines 31-39).
PHENO_INSTRUMENTS = ["basic_medical", "iq"]


def _measures(wgpf_server, instrument):
    return wgpf_server.client.get(
        "/api/v3/pheno_browser/measures",
        params={"dataset_id": "mini_pheno", "instrument": instrument},
    )


class TestPhenotypeImport:
    """RST lines 62-93: import the mini_pheno study, then ``wgpf run``
    serves it — visible on the Home Page and browsable in the Phenotype
    Browser."""

    def test_import_phenotypes_command_succeeds(self, phenotype_instance):
        assert_command_succeeds(
            phenotype_instance.pheno_import,
            rst_ref=f"{RST}:68",
            expectation=(
                "import_phenotypes input_phenotype_data/import_project.yaml "
                "succeeds"
            ),
        )

    def test_mini_pheno_visible_on_home_page(self, wgpf_server):
        resp = wgpf_server.client.get("/api/v3/datasets/visible")
        assert_dataset_visible(
            resp, "mini_pheno",
            rst_ref=f"{RST}:76",
            expectation=(
                "on the GPF instance Home Page, you should see the "
                "`mini_pheno` phenotype study"
            ),
        )

    def test_phenotype_browser_lists_imported_instruments(self, wgpf_server):
        # The Phenotype Browser tab (RST line 84) shows the imported
        # instruments; the instruments endpoint backs that listing.
        resp = wgpf_server.client.get(
            "/api/v3/pheno_browser/instruments",
            params={"dataset_id": "mini_pheno"},
        )
        assert_pheno_instruments_available(
            resp, PHENO_INSTRUMENTS,
            rst_ref=f"{RST}:84",
            expectation=(
                "following the link shows the Phenotype Browser tab with "
                "the imported data (the basic_medical + iq instruments)"
            ),
        )

    def test_phenotype_browser_search_returns_measures(self, wgpf_server):
        # RST lines 91-92: "you can search for phenotype instruments and
        # measures". The measures endpoint reads the browser DB that
        # `wgpf run` builds on startup — a non-empty result also confirms
        # that build happened (an un-built browser DB returns []).
        assert_pheno_measures_present(
            _measures(wgpf_server, "basic_medical"),
            rst_ref=f"{RST}:91",
            expectation=(
                "in the Phenotype Browser you can search for measures "
                "(searching the basic_medical instrument returns measures)"
            ),
        )

    def test_phenotype_browser_aggregated_figure_accessible(self, wgpf_server):
        # RST line 92: "see the aggregated figures for the measures". Each
        # measure record carries a `figure_distribution` image path built
        # by `wgpf run`; the image is served by the pheno-browser images
        # endpoint. Discover the path from the search result rather than
        # hard-coding it, then fetch the image through the API.
        resp = _measures(wgpf_server, "basic_medical")
        assert_pheno_measures_present(
            resp,
            rst_ref=f"{RST}:92",
            expectation="the Phenotype Browser lists measures with figures",
        )
        figures = [
            m["measure"].get("figure_distribution")
            for m in resp.json()
            if m.get("measure", {}).get("figure_distribution")
        ]
        if not figures:
            pytest.fail(
                f'DRIFT at {RST}:92 — "see the aggregated figures for the '
                f'measures"\n\n  No measure in the basic_medical search '
                f"result carried a `figure_distribution` path. `wgpf run` "
                f"builds these figures on startup; check the wgpf log dump "
                f"for a build_pheno_browser failure, or whether the measure "
                f"record's figure field was renamed.",
                pytrace=False,
            )
        image = wgpf_server.client.get(
            f"/api/v3/pheno_browser/images/mini_pheno/{figures[0]}",
        )
        assert_image_response_ok(
            image,
            rst_ref=f"{RST}:92",
            expectation=(
                "the aggregated figure for a measure is viewable through "
                "the pheno-browser images endpoint"
            ),
        )


class TestExampleDatasetPhenotype:
    """RST lines 96-122: attaching ``phenotype_data: mini_pheno`` to
    example_dataset enables the Phenotype Browser + Phenotype Tool tabs
    and the genotype-browser Pheno Measures filters."""

    def _description(self, wgpf_server):
        return wgpf_server.client.get("/api/v3/datasets/example_dataset")

    def test_example_dataset_has_phenotype_data_attached(self, wgpf_server):
        # The `phenotype_data: mini_pheno` line was added to the config by
        # the `phenotype_instance` fixture; confirm the attachment took.
        assert_dataset_description_flag(
            self._description(wgpf_server), "phenotype_data",
            rst_ref=f"{RST}:112",
            expectation=(
                "adding `phenotype_data: mini_pheno` to the example_dataset "
                "config attaches the phenotype study"
            ),
        )

    def test_example_dataset_phenotype_browser_enabled(self, wgpf_server):
        assert_dataset_description_flag(
            self._description(wgpf_server), "phenotype_browser",
            rst_ref=f"{RST}:114",
            expectation=(
                "the Phenotype Browser tab is enabled for the Example "
                "Dataset after attaching the phenotype database"
            ),
        )

    def test_example_dataset_phenotype_tool_enabled(self, wgpf_server):
        assert_dataset_description_flag(
            self._description(wgpf_server), "phenotype_tool",
            rst_ref=f"{RST}:114",
            expectation=(
                "the Phenotype Tool tab is enabled for the Example Dataset "
                "after attaching the phenotype database"
            ),
        )

    def test_example_dataset_has_family_pheno_filters(self, wgpf_server):
        assert_dataset_description_flag(
            self._description(wgpf_server),
            "genotype_browser_config.has_family_pheno_filters",
            rst_ref=f"{RST}:117",
            expectation=(
                "in the Genotype Browser, the Family Filters section has "
                "the Pheno Measures filters enabled"
            ),
        )

    def test_example_dataset_has_person_pheno_filters(self, wgpf_server):
        assert_dataset_description_flag(
            self._description(wgpf_server),
            "genotype_browser_config.has_person_pheno_filters",
            rst_ref=f"{RST}:118",
            expectation=(
                "in the Genotype Browser, the Person Filters section has "
                "the Pheno Measures filters enabled"
            ),
        )
