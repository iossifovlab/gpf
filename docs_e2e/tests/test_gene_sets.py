"""Guide-claim tests for getting_started_with_gene_sets.rst.

The gene-sets sub-guide covers three things, all against the same
``minimal_instance`` the earlier guides built:

1. **de Novo gene sets** — the GPF system auto-generates a collection of
   de Novo gene sets (LGDs, LGDs.Male, Missense, ...) for every genotype
   study with de Novo variants (``ssc_denovo``); no config needed. They
   show up in the study's Genotype Browser ``Genes > Gene Sets`` tab.
2. **pre-defined gene set collections** — adding a ``gene_sets_db`` block
   to gpf_instance.yaml makes the configured GRR gene set collections
   (``autism``, ``GO``) available.
3. **pre-defined gene scores** — adding a ``gene_scores_db`` block makes
   the configured GRR gene scores available.

The two config edits live in the session-scoped ``gene_sets_instance``
fixture (conftest.py); ``wgpf_server`` depends on it, so the single shared
server serves the gene-set/score-enabled instance. The de Novo gene sets
need no edit — they are generated for ``ssc_denovo`` (imported earlier in
the chain).

Strict mode (#871): the fixture only does what the guide tells the user to
do — the two yaml edits. The configured collections/scores are GRR
resources the server demand-pulls on first access; they are not in the
prewarmed cache, so the collection/score tests use a generous per-request
timeout to absorb that one-time cold pull.

Guide-drift fix shipped in the same PR (#879): the guide also listed
``gene_properties/gene_sets/relevant``, but that resource 404s in the
public GRR (resource + guide index.html link both gone), so it was removed
from the RST and is absent from the fixture config — these tests assert the
surviving ``autism`` + ``GO`` collections.

Each test maps to one discrete prose claim. ``rst_ref`` points at the line
in the guide source so a failure localizes the drift.
"""

from docs_e2e.guide_assertions import (
    assert_denovo_gene_sets_for_dataset,
    assert_gene_scores_available,
    assert_gene_set_collections_available,
)

RST = "getting_started_with_gene_sets.rst"

# The gene set collection ids the configured gene_sets_db resolves to.
# NB: the id is the collection's configured `id`, which differs from the
# GRR resource path — `gene_properties/gene_sets/GO_2024-06-17_release` has
# id `GO` (see the resource's genomic_resource.yaml).
GENE_SET_COLLECTIONS = ["autism", "GO"]

# The gene score ids the configured gene_scores_db resolves to — one stable
# id per configured GRR gene_score resource. A single resource can expose
# several scored columns (e.g. LGD -> LGD_score + LGD_rank); we assert one
# representative id per resource.
GENE_SCORES = [
    "Satterstrom_Buxbaum_Cell_2020_qval",    # Satterstrom_Buxbaum_Cell_2020
    "Iossifov_Wigler_PNAS_2015_post_noaut",  # Iossifov_Wigler_PNAS_2015
    "LGD_score",                             # LGD
    "LOEUF",                                 # LOEUF
]

# Cold demand-pull budget: the gene_sets_db / gene_scores_db GRR resources
# are not in the prewarmed cache, so the first request that touches each
# lazy collection pays a one-time GRR fetch. Well above the shared client's
# default 60s, comfortably under the build wall.
_COLD_PULL_TIMEOUT = 300


class TestDenovoGeneSets:
    """RST lines 19-44: the GPF system auto-generates de Novo gene sets for
    each genotype study with de Novo variants (``ssc_denovo``)."""

    def test_ssc_denovo_has_denovo_gene_sets(self, wgpf_server):
        # RST lines 34-37: navigating to the ssc_denovo Genotype Browser
        # `Genes > Gene Sets` tab shows the de Novo gene sets generated for
        # the study. The denovo_gene_sets_types endpoint backs that listing;
        # building the per-study cache here pays the (capped) de Novo query.
        resp = wgpf_server.client.get(
            "/api/v3/gene_sets/denovo_gene_sets_types",
            timeout=_COLD_PULL_TIMEOUT,
        )
        assert_denovo_gene_sets_for_dataset(
            resp, "ssc_denovo",
            rst_ref=f"{RST}:37",
            expectation=(
                "the GPF system generates de Novo gene sets for the "
                "ssc_denovo study (visible in its Genotype Browser "
                "`Genes > Gene Sets` tab)"
            ),
        )


class TestGeneSetCollections:
    """RST lines 47-103: adding the ``gene_sets_db`` block makes the
    configured pre-defined gene set collections available."""

    def test_configured_collections_available(self, wgpf_server):
        # RST lines 91-94: after restart the configured gene set collections
        # are available (shown in the ssc_denovo Genotype Browser
        # `Genes > Gene Sets` tab). First touch demand-pulls them from GRR.
        resp = wgpf_server.client.get(
            "/api/v3/gene_sets/gene_sets_collections",
            timeout=_COLD_PULL_TIMEOUT,
        )
        assert_gene_set_collections_available(
            resp, GENE_SET_COLLECTIONS,
            rst_ref=f"{RST}:93",
            expectation=(
                "the configured gene set collections (autism, GO) are "
                "available after adding the gene_sets_db block"
            ),
        )


class TestGeneScores:
    """RST lines 106-179: adding the ``gene_scores_db`` block makes the
    configured pre-defined gene scores available."""

    def test_configured_gene_scores_available(self, wgpf_server):
        # RST lines 165-168: after restart the configured gene scores are
        # available (shown in the ssc_denovo Genotype Browser
        # `Genes > Gene Scores` tab). First touch demand-pulls them from GRR.
        resp = wgpf_server.client.get(
            "/api/v3/gene_scores/",
            timeout=_COLD_PULL_TIMEOUT,
        )
        assert_gene_scores_available(
            resp, GENE_SCORES,
            rst_ref=f"{RST}:165",
            expectation=(
                "the configured gene scores are available after adding the "
                "gene_scores_db block"
            ),
        )
