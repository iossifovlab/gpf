"""Guide-claim tests for getting_started_with_enrichment.rst.

The enrichment sub-guide (~31 lines) covers the Enrichment Tool, which the
GPF system auto-enables for any genotype study with de Novo variants —
``ssc_denovo``, imported earlier in the chain. It makes three discrete
prose claims:

1. **the tool is enabled** (RST lines 4-5) — for each genotype study with
   de Novo variants the GPF system enables the Enrichment tool. The
   ``/api/v3/enrichment/models/<dataset_id>`` endpoint reports the study's
   enrichment configuration; a non-empty ``background`` list means the tool
   is enabled for that study.
2. **only the samocha background is configured by default** (RST note,
   lines 19-21) — for a de Novo study only one background model,
   ``enrichment/samocha_background``, is configured out of the box.
3. **tests can be run** (RST lines 26-27) — navigating to the Enrichment
   Tool page for ``ssc_denovo`` lets the user run enrichment tests. A
   ``POST /api/v3/enrichment/test`` with the study's default
   background/counting models and a gene set returns a result.

No conftest edit backs this guide: the Enrichment tool needs no
configuration (strict mode #871) — it auto-enables for de Novo studies, so
the tests run against ``ssc_denovo`` in the existing shared instance.

``enrichment/samocha_background`` lives in the GPF-specific public GRR
(``grr-gpf.iossifovlab.com``), not the general ``grr.iossifovlab.com``.
The suite's GRR definition (the denovo guide's "Caching GRR" block, mirrored
in conftest's ``denovo_instance``) is a ``group`` of both repos, so the
background resolves. It is not in the prewarmed cache (the prewarm only
caches the annotation pipeline's resources), so the first request that
touches it pays a one-time cold GRR pull — hence the generous per-request
timeout below.

Each test maps to one discrete prose claim. ``rst_ref`` points at the line
in the guide source so a failure localizes the drift.
"""

import pytest

from docs_e2e.guide_assertions import (
    assert_enrichment_models,
    assert_enrichment_test_result,
)

RST = "getting_started_with_enrichment.rst"

# The study the guide names — auto-enabled for the Enrichment tool because it
# carries de Novo variants. Imported by conftest's denovo_instance.
ENRICHMENT_DATASET = "ssc_denovo"

# The single background model the guide says is configured by default for a
# de Novo study (RST lines 19-21). The id is the GRR resource id.
SAMOCHA_BACKGROUND = "enrichment/samocha_background"

# A well-known autism gene used throughout the GPF guides; present in the
# gene models so the samocha background resolves an expected mutation count
# for it. The enrichment test computes expected-vs-observed regardless of
# whether the (variant-capped) ssc_denovo carries variants in this gene, so
# the result is non-empty for any valid gene symbol.
ENRICHMENT_GENE_SYMBOLS = ["CHD8"]

# Cold demand-pull budget: enrichment/samocha_background is not in the
# prewarmed cache, so the first request that loads it pays a one-time GRR
# fetch from grr-gpf.iossifovlab.com. Well above the shared client's default
# 60s, comfortably under the build wall.
_COLD_PULL_TIMEOUT = 300


@pytest.fixture(scope="module")
def enrichment_models_response(wgpf_server):
    """The enrichment models endpoint for ssc_denovo.

    Shared by the two models-backed claims (tool enabled + default
    background). The first call demand-pulls the samocha background, so the
    generous timeout applies here; the response is reused module-wide.
    """
    return wgpf_server.client.get(
        f"/api/v3/enrichment/models/{ENRICHMENT_DATASET}",
        timeout=_COLD_PULL_TIMEOUT,
    )


class TestEnrichmentToolEnabled:
    """RST lines 4-5: by default, for each genotype study with de Novo
    variants, the GPF system enables the Enrichment tool."""

    def test_enrichment_tool_enabled_for_ssc_denovo(
            self, enrichment_models_response):
        assert_enrichment_models(
            enrichment_models_response,
            rst_ref=f"{RST}:4",
            expectation=(
                "the GPF system enables the Enrichment tool for the "
                "ssc_denovo study (it has de Novo variants)"
            ),
        )


class TestDefaultBackgroundModel:
    """RST lines 19-21: by default, for studies with de Novo variants, only
    one background model is configured: enrichment/samocha_background."""

    def test_only_samocha_background_configured(
            self, enrichment_models_response):
        assert_enrichment_models(
            enrichment_models_response,
            require_background_ids=[SAMOCHA_BACKGROUND],
            rst_ref=f"{RST}:20",
            expectation=(
                "by default only the enrichment/samocha_background background "
                "model is configured for a de Novo study"
            ),
        )


class TestRunEnrichmentTest:
    """RST lines 26-27: navigating to the Enrichment Tool page for ssc_denovo
    lets the user run different enrichment tests."""

    def test_enrichment_test_runs(
            self, wgpf_server, enrichment_models_response):
        # Drive the tool exactly as the SPA does: pick the study's default
        # background + counting models (the guide says samocha is the only
        # background), supply a gene set, and POST. A non-empty result means
        # the tool ran a test — the guide's "you will be able to run different
        # tests" claim.
        models = enrichment_models_response.json()
        resp = wgpf_server.client.post(
            "/api/v3/enrichment/test",
            json={
                "datasetId": ENRICHMENT_DATASET,
                "enrichmentBackgroundModel": models["defaultBackground"],
                "enrichmentCountingModel": models["defaultCounting"],
                "geneSymbols": ENRICHMENT_GENE_SYMBOLS,
            },
            timeout=_COLD_PULL_TIMEOUT,
        )
        assert_enrichment_test_result(
            resp,
            rst_ref=f"{RST}:26",
            expectation=(
                "on the Enrichment Tool page for ssc_denovo the user can run "
                "enrichment tests and get results"
            ),
        )
