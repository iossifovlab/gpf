"""Guide-claim tests for getting_started_with_annotation.rst.

The annotation section tells the user to append a gnomAD + ClinVar
annotation block to ``minimal_instance/gpf_instance.yaml`` and re-run
``wgpf run`` — which re-annotates the already-imported genotype data.
The variants then carry three additional attributes
(``gnomad_v4_genome_ALL_af``, ``CLNSIG``, ``CLNDN``) that are included
in genotype-browser downloads and usable as genomic-score filters.

The config edit lives in the session-scoped ``annotated_instance``
fixture (conftest.py); ``wgpf_server`` depends on it, so the single
shared server reflects the annotated state. Strict mode (#871): the
fixture only does what the guide tells the user to do — edit the yaml;
re-annotation is triggered by wgpf itself.

Each test maps to one discrete prose claim. ``rst_ref`` points at the
line in the guide source so a failure localizes the drift.
"""

from docs_e2e.guide_assertions import (
    assert_dataset_visible,
    assert_download_has_columns,
    assert_download_trailing_columns,
    assert_genomic_score_available,
)

RST = "getting_started_with_annotation.rst"

# The three attributes the annotation produces (RST lines 67-69).
ANNOTATION_ATTRIBUTES = ["gnomad_v4_genome_ALL_af", "CLNSIG", "CLNDN"]


class TestReannotation:
    """RST lines 57-62: ``wgpf run`` re-annotates genotype data that is
    not up to date and serves the annotated instance."""

    def test_wgpf_run_serves_reannotated_instance(self, wgpf_server):
        # The annotation block was appended to gpf_instance.yaml by the
        # `annotated_instance` fixture; `wgpf_server` then started
        # `wgpf run`, which re-annotated on startup. If re-annotation
        # had failed, the server would not have become ready and this
        # (and every server-backed test) would fail at fixture setup.
        # Assert the instance still serves the example dataset.
        resp = wgpf_server.client.get("/api/v3/datasets/visible")
        assert_dataset_visible(
            resp, "example_dataset",
            rst_ref=f"{RST}:57",
            expectation=(
                "after the annotation block is added, `wgpf run` "
                "re-annotates and serves the instance with example_dataset "
                "still available"
            ),
        )


class TestAnnotationDownloadColumns:
    """RST lines 64-92: the re-annotated variants carry the gnomAD +
    ClinVar attributes, included in the Genotype Browser download as
    the last columns."""

    def _download(self, wgpf_server):
        # The guide's "Download" button (RST line 89) maps to the
        # query-download endpoint. No filter — the whole Example
        # Dataset, so every annotation column is exercised.
        return wgpf_server.client.post(
            "/api/v3/genotype_browser/query-download",
            json={"datasetId": "example_dataset"},
        )

    def test_download_has_gnomad_attribute(self, wgpf_server):
        assert_download_has_columns(
            self._download(wgpf_server), ["gnomad_v4_genome_ALL_af"],
            rst_ref=f"{RST}:67",
            expectation=(
                "the downloaded variants file includes the "
                "`gnomad_v4_genome_ALL_af` attribute from gnomAD annotation"
            ),
        )

    def test_download_has_clnsig_attribute(self, wgpf_server):
        assert_download_has_columns(
            self._download(wgpf_server), ["CLNSIG"],
            rst_ref=f"{RST}:68",
            expectation=(
                "the downloaded variants file includes the `CLNSIG` "
                "attribute from ClinVar annotation"
            ),
        )

    def test_download_has_clndn_attribute(self, wgpf_server):
        assert_download_has_columns(
            self._download(wgpf_server), ["CLNDN"],
            rst_ref=f"{RST}:69",
            expectation=(
                "the downloaded variants file includes the `CLNDN` "
                "attribute from ClinVar annotation"
            ),
        )

    def test_annotation_attributes_are_last_columns(self, wgpf_server):
        assert_download_trailing_columns(
            self._download(wgpf_server), ANNOTATION_ATTRIBUTES,
            rst_ref=f"{RST}:91",
            expectation=(
                "attributes from the annotation are included as the last "
                "columns in the downloaded file"
            ),
        )


class TestAnnotationGenomicScores:
    """RST lines 77-78: the annotation attributes are usable as genomic
    score query filters (registered in the genomic-scores registry)."""

    def _genomic_scores(self, wgpf_server):
        return wgpf_server.client.get("/api/v3/genomic_scores/")

    def test_gnomad_is_queryable_genomic_score(self, wgpf_server):
        assert_genomic_score_available(
            self._genomic_scores(wgpf_server), "gnomad_v4_genome_ALL_af",
            rst_ref=f"{RST}:77",
            expectation=(
                "the variants can be queried using the "
                "`gnomad_v4_genome_ALL_af` genomic score"
            ),
        )

    def test_clnsig_is_queryable_genomic_score(self, wgpf_server):
        assert_genomic_score_available(
            self._genomic_scores(wgpf_server), "CLNSIG",
            rst_ref=f"{RST}:77",
            expectation=(
                "the variants can be queried using the `CLNSIG` genomic score"
            ),
        )

    def test_clndn_is_queryable_genomic_score(self, wgpf_server):
        assert_genomic_score_available(
            self._genomic_scores(wgpf_server), "CLNDN",
            rst_ref=f"{RST}:78",
            expectation=(
                "the variants can be queried using the `CLNDN` genomic score"
            ),
        )
