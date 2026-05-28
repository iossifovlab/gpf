"""Unit tests for docs_e2e.guide_assertions.

These run in plain Python — no conda env, no wgpf, no GPF imports.
Mock objects use stdlib SimpleNamespace so the test file has no
runtime deps beyond pytest.
"""

from types import SimpleNamespace

import pytest

from docs_e2e.guide_assertions import (
    assert_command_succeeds,
    assert_dataset_visible,
    assert_download_has_columns,
    assert_download_trailing_columns,
    assert_file_created,
    assert_genomic_score_available,
    assert_query_returned_variants,
)


def _tsv(*headers):
    """A download response whose body is a TSV with these headers."""
    return _FakeResponse(200, text="\t".join(headers) + "\nrow1\trow2\n")


# A realistic example_dataset download header: the fixed genotype
# columns followed by the three annotation attributes as trailing
# columns (see getting_started_with_annotation.rst).
_ANNOTATED_HEADER = [
    "family id", "study", "location", "variant", "worst effect", "genes",
    "gnomad_v4_genome_ALL_af", "CLNDN", "CLNSIG",
]


class _FakeResponse:
    """Minimal duck-typed httpx.Response stand-in."""

    def __init__(self, status_code, json_body=None, text=""):
        self.status_code = status_code
        self._json = json_body
        self.text = text

    def json(self):
        if self._json is None:
            raise ValueError("no json body")
        return self._json


def _ok_result():
    return SimpleNamespace(
        returncode=0,
        args=["echo", "hi"],
        stdout=b"hi\n",
        stderr=b"",
    )


def _failed_result():
    return SimpleNamespace(
        returncode=2,
        args=["import_genotypes", "denovo_example.yaml"],
        stdout=b"some output\n",
        stderr=b"error: unrecognized arguments: --bad-flag\n",
    )


class TestAssertCommandSucceeds:
    def test_passes_silently_on_zero_exit_code(self):
        # No exception expected.
        assert_command_succeeds(
            _ok_result(),
            rst_ref="getting_started.rst:181",
            expectation="import_genotypes succeeds",
        )

    def test_raises_assertion_error_on_nonzero_exit_code(self):
        with pytest.raises(AssertionError):
            assert_command_succeeds(
                _failed_result(),
                rst_ref="getting_started.rst:181",
                expectation="import_genotypes succeeds",
            )

    def test_failure_message_carries_full_diagnostic(self):
        with pytest.raises(AssertionError) as exc_info:
            assert_command_succeeds(
                _failed_result(),
                rst_ref="getting_started.rst:181",
                expectation="import_genotypes succeeds",
            )
        message = str(exc_info.value)
        # rst ref so the operator can jump straight to the source line
        assert "getting_started.rst:181" in message
        # paraphrased guide claim
        assert "import_genotypes succeeds" in message
        # actual exit code
        assert "exit code 2" in message
        # the failing command line, so the operator can re-run it
        assert "import_genotypes denovo_example.yaml" in message
        # stderr surfaced — the error message itself is the most
        # actionable piece of context
        assert "unrecognized arguments: --bad-flag" in message
        # triage hint disambiguating guide-drift vs. code-regression
        assert "Triage" in message


class TestAssertFileCreated:
    def test_passes_silently_when_path_exists(self, tmp_path):
        target = tmp_path / "created.yaml"
        target.write_text("ok")
        assert_file_created(
            target,
            rst_ref="getting_started.rst:199",
            expectation="study YAML written under studies/",
        )

    def test_raises_assertion_error_when_path_missing(self, tmp_path):
        target = tmp_path / "missing.yaml"
        with pytest.raises(AssertionError):
            assert_file_created(
                target,
                rst_ref="getting_started.rst:199",
                expectation="study YAML written under studies/",
            )

    def test_failure_message_carries_diagnostic_when_prior_command_ok(
            self, tmp_path,
    ):
        target = tmp_path / "missing.yaml"
        prior = SimpleNamespace(
            returncode=0,
            args=["import_genotypes", "denovo_example.yaml"],
            stdout=b"import finished\n",
            stderr=b"",
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_file_created(
                target,
                rst_ref="getting_started.rst:199",
                expectation="study YAML written under studies/",
                after_command=prior,
            )
        message = str(exc_info.value)
        assert "getting_started.rst:199" in message
        assert "study YAML written under studies/" in message
        assert str(target) in message
        # Triage points at code/import-behavior drift because the
        # prior step succeeded — file should be there but isn't.
        assert "Triage" in message
        assert "code regression" in message or "import behavior" in message

    def test_failure_message_blames_prior_command_when_it_failed(
            self, tmp_path,
    ):
        target = tmp_path / "missing.yaml"
        prior = SimpleNamespace(
            returncode=2,
            args=["import_genotypes", "denovo_example.yaml"],
            stdout=b"",
            stderr=b"error: bad config\n",
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_file_created(
                target,
                rst_ref="getting_started.rst:199",
                expectation="study YAML written under studies/",
                after_command=prior,
            )
        message = str(exc_info.value)
        # When the prior command failed, triage redirects there
        # rather than blaming the (absent) file's creator.
        assert "exit code 2" in message
        assert "bad config" in message
        assert "fix that first" in message.lower() \
            or "prior command failed" in message.lower()


class TestAssertDatasetVisible:
    def test_passes_when_dataset_id_present(self):
        # /api/v3/datasets/visible returns a list of dataset-id
        # STRINGS — this is the real on-the-wire shape.
        resp = _FakeResponse(
            200,
            json_body=["denovo_example", "vcf_example"],
        )
        assert_dataset_visible(
            resp, "denovo_example",
            rst_ref="getting_started.rst:213",
            expectation="home page lists denovo_example",
        )

    def test_passes_when_response_is_list_of_dicts(self):
        # Tolerate a richer {"id": ...} shape too, for callers that
        # pass a response from a different datasets endpoint.
        resp = _FakeResponse(
            200,
            json_body=[
                {"id": "denovo_example", "name": "De novo example"},
                {"id": "vcf_example", "name": "VCF example"},
            ],
        )
        assert_dataset_visible(
            resp, "denovo_example",
            rst_ref="getting_started.rst:213",
            expectation="home page lists denovo_example",
        )

    def test_raises_when_dataset_id_missing(self):
        resp = _FakeResponse(
            200,
            json_body=["vcf_example"],
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_dataset_visible(
                resp, "denovo_example",
                rst_ref="getting_started.rst:213",
                expectation="home page lists denovo_example",
            )
        message = str(exc_info.value)
        assert "getting_started.rst:213" in message
        assert "denovo_example" in message
        # Names the datasets that ARE visible, so the operator can
        # tell at a glance whether nothing was imported, the id was
        # renamed, etc.
        assert "vcf_example" in message
        assert "Triage" in message

    def test_raises_when_response_is_http_error(self):
        resp = _FakeResponse(
            500,
            text="Internal Server Error: traceback...",
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_dataset_visible(
                resp, "denovo_example",
                rst_ref="getting_started.rst:213",
                expectation="home page lists denovo_example",
            )
        message = str(exc_info.value)
        assert "500" in message
        assert "Internal Server Error" in message
        # When the server is broken, triage points there, not at
        # the guide.
        assert "server" in message.lower() or "backend" in message.lower()


class TestAssertQueryReturnedVariants:
    def test_passes_when_response_contains_variants(self):
        resp = _FakeResponse(
            200,
            json_body=[
                {"family_id": "f1", "gene_symbols": ["CHD8"]},
                {"family_id": "f2", "gene_symbols": ["CHD8"]},
                {"family_id": "f3", "gene_symbols": ["CHD8"]},
            ],
        )
        # Default min_count=1 passes here.
        assert_query_returned_variants(
            resp,
            rst_ref="getting_started.rst:288",
            expectation="gene-browser CHD8 query returns variants",
        )

    def test_raises_when_response_is_empty_list(self):
        resp = _FakeResponse(200, json_body=[])
        with pytest.raises(AssertionError) as exc_info:
            assert_query_returned_variants(
                resp,
                rst_ref="getting_started.rst:288",
                expectation="gene-browser CHD8 query returns variants",
            )
        message = str(exc_info.value)
        assert "getting_started.rst:288" in message
        assert "0 variant" in message  # matches "0 variant(s)" or "0 variants"
        # Empty result is most often an import issue or a filter
        # mismatch, not a server bug.
        assert "Triage" in message

    def test_raises_on_http_error(self):
        resp = _FakeResponse(503, text="Service Unavailable")
        with pytest.raises(AssertionError) as exc_info:
            assert_query_returned_variants(
                resp,
                rst_ref="getting_started.rst:288",
                expectation="gene-browser CHD8 query returns variants",
            )
        message = str(exc_info.value)
        assert "503" in message
        assert "Service Unavailable" in message

    def test_respects_custom_min_count(self):
        resp = _FakeResponse(
            200,
            json_body=[{"family_id": "f1", "gene_symbols": ["CHD8"]}],
        )
        # Got 1 but expected at least 3 — should raise.
        with pytest.raises(AssertionError) as exc_info:
            assert_query_returned_variants(
                resp, min_count=3,
                rst_ref="getting_started.rst:288",
                expectation="at least 3 CHD8 variants present",
            )
        message = str(exc_info.value)
        assert "at least 3" in message
        assert "1 variant" in message


class TestAssertDownloadHasColumns:
    def test_passes_when_all_columns_present(self):
        resp = _tsv(*_ANNOTATED_HEADER)
        assert_download_has_columns(
            resp, ["gnomad_v4_genome_ALL_af", "CLNSIG", "CLNDN"],
            rst_ref="getting_started_with_annotation.rst:67",
            expectation="download includes annotation attributes",
        )

    def test_raises_when_a_column_missing(self):
        # gnomAD attribute absent — annotation did not take effect.
        resp = _tsv(
            "family id", "study", "worst effect", "genes",
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_download_has_columns(
                resp, ["gnomad_v4_genome_ALL_af"],
                rst_ref="getting_started_with_annotation.rst:67",
                expectation="download includes gnomad_v4_genome_ALL_af",
            )
        message = str(exc_info.value)
        assert "getting_started_with_annotation.rst:67" in message
        assert "gnomad_v4_genome_ALL_af" in message
        # The actual header is surfaced so the operator can see what
        # columns DID come through.
        assert "worst effect" in message
        assert "Triage" in message

    def test_raises_on_http_error(self):
        resp = _FakeResponse(500, text="Internal Server Error")
        with pytest.raises(AssertionError) as exc_info:
            assert_download_has_columns(
                resp, ["gnomad_v4_genome_ALL_af"],
                rst_ref="getting_started_with_annotation.rst:67",
                expectation="download includes gnomad_v4_genome_ALL_af",
            )
        message = str(exc_info.value)
        assert "500" in message
        assert "server" in message.lower() or "backend" in message.lower()


class TestAssertDownloadTrailingColumns:
    def test_passes_when_columns_are_trailing_any_order(self):
        # Live order is gnomad, CLNDN, CLNSIG — the helper is
        # order-insensitive among the trailing columns, so passing
        # the guide's prose order (CLNSIG before CLNDN) still passes.
        resp = _tsv(*_ANNOTATED_HEADER)
        assert_download_trailing_columns(
            resp, ["gnomad_v4_genome_ALL_af", "CLNSIG", "CLNDN"],
            rst_ref="getting_started_with_annotation.rst:91",
            expectation="annotation attributes are the last columns",
        )

    def test_raises_when_a_column_trails_the_annotation_block(self):
        # An extra column appended after the annotation block — the
        # "last columns" claim no longer holds.
        resp = _tsv(
            "family id", "gnomad_v4_genome_ALL_af", "CLNDN", "CLNSIG",
            "some_new_trailing_column",
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_download_trailing_columns(
                resp, ["gnomad_v4_genome_ALL_af", "CLNSIG", "CLNDN"],
                rst_ref="getting_started_with_annotation.rst:91",
                expectation="annotation attributes are the last columns",
            )
        message = str(exc_info.value)
        assert "getting_started_with_annotation.rst:91" in message
        assert "some_new_trailing_column" in message
        assert "Triage" in message


class TestAssertGenomicScoreAvailable:
    def test_passes_when_score_present_dict_shape(self):
        resp = _FakeResponse(
            200,
            json_body=[
                {"score": "gnomad_v4_genome_ALL_af"},
                {"score": "CLNDN"},
                {"score": "CLNSIG"},
            ],
        )
        assert_genomic_score_available(
            resp, "CLNSIG",
            rst_ref="getting_started_with_annotation.rst:77",
            expectation="CLNSIG is queryable as a genomic score",
        )

    def test_passes_when_score_present_string_shape(self):
        resp = _FakeResponse(
            200,
            json_body=["gnomad_v4_genome_ALL_af", "CLNDN", "CLNSIG"],
        )
        assert_genomic_score_available(
            resp, "gnomad_v4_genome_ALL_af",
            rst_ref="getting_started_with_annotation.rst:77",
            expectation="gnomad score is queryable",
        )

    def test_raises_when_score_missing(self):
        resp = _FakeResponse(
            200,
            json_body=[{"score": "gnomad_v4_genome_ALL_af"}],
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_genomic_score_available(
                resp, "CLNSIG",
                rst_ref="getting_started_with_annotation.rst:77",
                expectation="CLNSIG is queryable as a genomic score",
            )
        message = str(exc_info.value)
        assert "getting_started_with_annotation.rst:77" in message
        assert "CLNSIG" in message
        # Lists what IS available so the operator can spot a rename.
        assert "gnomad_v4_genome_ALL_af" in message
        assert "Triage" in message

    def test_raises_on_http_error(self):
        resp = _FakeResponse(503, text="Service Unavailable")
        with pytest.raises(AssertionError) as exc_info:
            assert_genomic_score_available(
                resp, "CLNSIG",
                rst_ref="getting_started_with_annotation.rst:77",
                expectation="CLNSIG is queryable as a genomic score",
            )
        message = str(exc_info.value)
        assert "503" in message
