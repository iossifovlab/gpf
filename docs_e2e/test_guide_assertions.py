"""Unit tests for docs_e2e.guide_assertions.

These run in plain Python — no conda env, no wgpf, no GPF imports.
Mock objects use stdlib SimpleNamespace so the test file has no
runtime deps beyond pytest.
"""

from types import SimpleNamespace

import pytest

from docs_e2e.guide_assertions import (
    assert_command_succeeds,
    assert_dataset_description_flag,
    assert_dataset_visible,
    assert_denovo_gene_sets_for_dataset,
    assert_download_has_columns,
    assert_download_trailing_columns,
    assert_enrichment_models,
    assert_enrichment_test_result,
    assert_file_created,
    assert_gene_profile_for_gene,
    assert_gene_profile_table_rows,
    assert_gene_profiles_configured,
    assert_gene_scores_available,
    assert_gene_set_collections_available,
    assert_genomic_score_available,
    assert_image_response_ok,
    assert_pheno_instruments_available,
    assert_pheno_measures_present,
    assert_preview_table_column_group,
    assert_python_snippet_output,
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

    def __init__(
        self, status_code, json_body=None, text="",
        content=b"", headers=None,
    ):
        self.status_code = status_code
        self._json = json_body
        self.text = text
        self.content = content
        self.headers = headers or {}

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


class TestAssertPhenoInstrumentsAvailable:
    def test_passes_when_all_instruments_present(self):
        resp = _FakeResponse(
            200,
            json_body={
                "instruments": ["basic_medical", "iq"],
                "default": "basic_medical",
            },
        )
        assert_pheno_instruments_available(
            resp, ["basic_medical", "iq"],
            rst_ref="getting_started_with_phenotype_data.rst:84",
            expectation="Phenotype Browser shows the imported instruments",
        )

    def test_raises_when_an_instrument_missing(self):
        resp = _FakeResponse(
            200,
            json_body={"instruments": ["basic_medical"], "default":
                       "basic_medical"},
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_pheno_instruments_available(
                resp, ["basic_medical", "iq"],
                rst_ref="getting_started_with_phenotype_data.rst:84",
                expectation="Phenotype Browser shows the imported instruments",
            )
        message = str(exc_info.value)
        assert "getting_started_with_phenotype_data.rst:84" in message
        assert "iq" in message
        # The instruments that ARE present are surfaced.
        assert "basic_medical" in message
        assert "Triage" in message

    def test_raises_on_http_error(self):
        resp = _FakeResponse(500, text="Internal Server Error")
        with pytest.raises(AssertionError) as exc_info:
            assert_pheno_instruments_available(
                resp, ["basic_medical"],
                rst_ref="getting_started_with_phenotype_data.rst:84",
                expectation="Phenotype Browser shows the imported instruments",
            )
        message = str(exc_info.value)
        assert "500" in message
        assert "server" in message.lower() or "backend" in message.lower()


class TestAssertDatasetDescriptionFlag:
    def _described(self, **inner):
        # The single-dataset endpoint wraps the description in "data".
        return _FakeResponse(200, json_body={"data": inner})

    def test_passes_when_top_level_flag_truthy(self):
        resp = self._described(
            id="example_dataset", phenotype_tool=True,
        )
        assert_dataset_description_flag(
            resp, "phenotype_tool",
            rst_ref="getting_started_with_phenotype_data.rst:114",
            expectation="Phenotype Tool tab enabled for Example Dataset",
        )

    def test_passes_when_nested_flag_truthy(self):
        resp = self._described(
            id="example_dataset",
            genotype_browser_config={"has_person_pheno_filters": True},
        )
        assert_dataset_description_flag(
            resp, "genotype_browser_config.has_person_pheno_filters",
            rst_ref="getting_started_with_phenotype_data.rst:118",
            expectation="Person Filters expose Pheno Measures filters",
        )

    def test_raises_when_flag_falsy(self):
        resp = self._described(
            id="example_dataset", phenotype_tool=False,
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_dataset_description_flag(
                resp, "phenotype_tool",
                rst_ref="getting_started_with_phenotype_data.rst:114",
                expectation="Phenotype Tool tab enabled for Example Dataset",
            )
        message = str(exc_info.value)
        assert "getting_started_with_phenotype_data.rst:114" in message
        assert "phenotype_tool" in message
        assert "Triage" in message

    def test_raises_when_flag_absent(self):
        resp = self._described(id="example_dataset")
        with pytest.raises(AssertionError) as exc_info:
            assert_dataset_description_flag(
                resp, "genotype_browser_config.has_family_pheno_filters",
                rst_ref="getting_started_with_phenotype_data.rst:117",
                expectation="Family Filters expose Pheno Measures filters",
            )
        message = str(exc_info.value)
        assert "absent" in message
        # Surfaces the keys that WERE present, to spot a rename.
        assert "id" in message

    def test_raises_on_http_error(self):
        resp = _FakeResponse(404, text="Dataset not found")
        with pytest.raises(AssertionError) as exc_info:
            assert_dataset_description_flag(
                resp, "phenotype_browser",
                rst_ref="getting_started_with_phenotype_data.rst:114",
                expectation="Phenotype Browser tab enabled",
            )
        message = str(exc_info.value)
        assert "404" in message


class TestAssertPhenoMeasuresPresent:
    def _measures(self, *names):
        return _FakeResponse(
            200,
            json_body=[{"measure": {"measure_id": n}} for n in names],
        )

    def test_passes_when_measures_returned(self):
        assert_pheno_measures_present(
            self._measures("basic_medical.age", "basic_medical.weight"),
            rst_ref="getting_started_with_phenotype_data.rst:91",
            expectation="searching basic_medical returns measures",
        )

    def test_raises_when_no_measures(self):
        # An empty browser DB (wgpf run did not build it) yields [].
        with pytest.raises(AssertionError) as exc_info:
            assert_pheno_measures_present(
                _FakeResponse(200, json_body=[]),
                rst_ref="getting_started_with_phenotype_data.rst:91",
                expectation="searching basic_medical returns measures",
            )
        message = str(exc_info.value)
        assert "0 measure" in message
        assert "build_pheno_browser" in message
        assert "Triage" in message

    def test_raises_on_http_error(self):
        with pytest.raises(AssertionError) as exc_info:
            assert_pheno_measures_present(
                _FakeResponse(500, text="Internal Server Error"),
                rst_ref="getting_started_with_phenotype_data.rst:91",
                expectation="searching basic_medical returns measures",
            )
        message = str(exc_info.value)
        assert "500" in message


class TestAssertImageResponseOk:
    def test_passes_on_image_bytes(self):
        resp = _FakeResponse(
            200, content=b"\xff\xd8\xff\xe0jpegdata",
            headers={"content-type": "image/jpeg"},
        )
        assert_image_response_ok(
            resp,
            rst_ref="getting_started_with_phenotype_data.rst:91",
            expectation="the measure's aggregated figure is viewable",
        )

    def test_raises_on_404(self):
        # Figure file missing — wgpf run did not build the images.
        resp = _FakeResponse(404, text="not found")
        with pytest.raises(AssertionError) as exc_info:
            assert_image_response_ok(
                resp,
                rst_ref="getting_started_with_phenotype_data.rst:91",
                expectation="the measure's aggregated figure is viewable",
            )
        message = str(exc_info.value)
        assert "404" in message

    def test_raises_when_200_but_not_an_image(self):
        # 200 with an empty body / non-image content-type is not a figure.
        resp = _FakeResponse(
            200, content=b"", headers={"content-type": "text/html"},
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_image_response_ok(
                resp,
                rst_ref="getting_started_with_phenotype_data.rst:91",
                expectation="the measure's aggregated figure is viewable",
            )
        message = str(exc_info.value)
        assert "text/html" in message


class TestAssertPreviewTableColumnGroup:
    _RST = "getting_started_with_preview_columns.rst"

    def _description(self, *table_columns):
        # The single-dataset endpoint wraps the description in "data";
        # the resolved preview layout is genotype_browser_config.table_columns.
        return _FakeResponse(200, json_body={"data": {
            "id": "example_dataset",
            "genotype_browser_config": {"table_columns": list(table_columns)},
        }})

    def _group(self, name, *members):
        # A column-group table_columns entry as build_genotype_data_description
        # emits it: {"name": ..., "columns": [{"name", "source"}, ...]}.
        return {
            "name": name,
            "columns": [
                {"name": disp, "source": src} for disp, src in members
            ],
        }

    def test_passes_when_group_present(self):
        resp = self._description(
            self._group("ClinVar", ("CLNSIG", "CLNSIG"), ("CLNDN", "CLNDN")),
        )
        assert_preview_table_column_group(
            resp, "ClinVar",
            rst_ref=f"{self._RST}:67",
            expectation="ClinVar column group appears in the preview table",
        )

    def test_passes_when_expected_sources_present(self):
        resp = self._description(
            self._group("ClinVar", ("CLNSIG", "CLNSIG"), ("CLNDN", "CLNDN")),
        )
        assert_preview_table_column_group(
            resp, "ClinVar",
            expected_sources=["CLNSIG", "CLNDN"],
            rst_ref=f"{self._RST}:73",
            expectation="ClinVar group carries CLNSIG + CLNDN",
        )

    def test_passes_when_sources_a_subset(self):
        # frequency carries allele_freq too; only gnomad is asserted.
        resp = self._description(
            self._group(
                "frequency",
                ("allele freq", "allele_freq"),
                ("gnomad_v4_genome_ALL_af", "gnomad_v4_genome_ALL_af"),
            ),
        )
        assert_preview_table_column_group(
            resp, "frequency",
            expected_sources=["gnomad_v4_genome_ALL_af"],
            rst_ref=f"{self._RST}:69",
            expectation="frequency group includes the gnomAD frequency",
        )

    def test_passes_when_expected_column_names_present(self):
        resp = self._description(
            self._group(
                "Proband IQ",
                ("Verbal IQ", "iq.verbal_iq"),
                ("Non-Verbal IQ", "iq.non_verbal_iq"),
            ),
        )
        assert_preview_table_column_group(
            resp, "Proband IQ",
            expected_sources=["iq.verbal_iq", "iq.non_verbal_iq"],
            expected_column_names=["Verbal IQ", "Non-Verbal IQ"],
            rst_ref=f"{self._RST}:159",
            expectation="Proband IQ group carries both IQ measures",
        )

    def test_raises_when_group_absent(self):
        resp = self._description(
            self._group("frequency", ("allele freq", "allele_freq")),
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_preview_table_column_group(
                resp, "ClinVar",
                rst_ref=f"{self._RST}:67",
                expectation="ClinVar column group appears in the preview table",
            )
        message = str(exc_info.value)
        assert f"{self._RST}:67" in message
        assert "ClinVar" in message
        # Surfaces the groups that WERE present, to spot a rename.
        assert "frequency" in message
        assert "Triage" in message

    def test_raises_when_a_source_missing(self):
        resp = self._description(
            self._group("ClinVar", ("CLNSIG", "CLNSIG")),
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_preview_table_column_group(
                resp, "ClinVar",
                expected_sources=["CLNSIG", "CLNDN"],
                rst_ref=f"{self._RST}:73",
                expectation="ClinVar group carries CLNSIG + CLNDN",
            )
        message = str(exc_info.value)
        assert "CLNDN" in message
        assert "missing" in message
        assert "Triage" in message

    def test_raises_when_a_column_name_missing(self):
        resp = self._description(
            self._group("Proband IQ", ("Verbal IQ", "iq.verbal_iq")),
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_preview_table_column_group(
                resp, "Proband IQ",
                expected_column_names=["Verbal IQ", "Non-Verbal IQ"],
                rst_ref=f"{self._RST}:159",
                expectation="Proband IQ group shows both IQ display names",
            )
        message = str(exc_info.value)
        assert "Non-Verbal IQ" in message

    def test_raises_on_http_error(self):
        resp = _FakeResponse(404, text="Dataset not found")
        with pytest.raises(AssertionError) as exc_info:
            assert_preview_table_column_group(
                resp, "ClinVar",
                rst_ref=f"{self._RST}:67",
                expectation="ClinVar column group appears in the preview table",
            )
        message = str(exc_info.value)
        assert "404" in message
        assert "Triage" in message


_GS_RST = "getting_started_with_gene_sets.rst"


class TestAssertGeneSetCollectionsAvailable:
    def test_passes_when_all_collections_present(self):
        resp = _FakeResponse(
            200,
            json_body=[
                {"name": "autism"}, {"name": "denovo"}, {"name": "GO"},
            ],
        )
        assert_gene_set_collections_available(
            resp, ["autism", "GO"],
            rst_ref=f"{_GS_RST}:95",
            expectation="configured gene set collections are available",
        )

    def test_raises_when_collection_missing(self):
        # Models the relevant-404 drift: a configured collection that did
        # not load is absent from the list.
        resp = _FakeResponse(
            200,
            json_body=[{"name": "autism"}, {"name": "GO"}],
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_set_collections_available(
                resp, ["autism", "relevant", "GO"],
                rst_ref=f"{_GS_RST}:95",
                expectation="configured gene set collections are available",
            )
        message = str(exc_info.value)
        assert f"{_GS_RST}:95" in message
        assert "relevant" in message
        # Lists what IS available so the operator can spot the gap.
        assert "autism" in message
        assert "Triage" in message

    def test_raises_on_http_error(self):
        resp = _FakeResponse(500, text="Internal Server Error")
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_set_collections_available(
                resp, ["autism"],
                rst_ref=f"{_GS_RST}:95",
                expectation="configured gene set collections are available",
            )
        assert "500" in str(exc_info.value)


class TestAssertGeneScoresAvailable:
    def test_passes_when_all_scores_present(self):
        resp = _FakeResponse(
            200,
            json_body=[
                {"score": "LGD_score"}, {"score": "RVIS score"},
                {"score": "LOEUF"},
            ],
        )
        assert_gene_scores_available(
            resp, ["LGD_score", "LOEUF"],
            rst_ref=f"{_GS_RST}:171",
            expectation="configured gene scores are available",
        )

    def test_raises_when_score_missing(self):
        resp = _FakeResponse(
            200,
            json_body=[{"score": "LGD_score"}],
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_scores_available(
                resp, ["LGD_score", "LOEUF"],
                rst_ref=f"{_GS_RST}:171",
                expectation="configured gene scores are available",
            )
        message = str(exc_info.value)
        assert f"{_GS_RST}:171" in message
        assert "LOEUF" in message
        assert "LGD_score" in message
        assert "Triage" in message

    def test_raises_on_http_error(self):
        resp = _FakeResponse(503, text="Service Unavailable")
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_scores_available(
                resp, ["LOEUF"],
                rst_ref=f"{_GS_RST}:171",
                expectation="configured gene scores are available",
            )
        assert "503" in str(exc_info.value)


class TestAssertDenovoGeneSetsForDataset:
    def test_passes_when_dataset_present(self):
        resp = _FakeResponse(
            200,
            json_body=[
                {"datasetId": "denovo_example"},
                {"datasetId": "ssc_denovo"},
            ],
        )
        assert_denovo_gene_sets_for_dataset(
            resp, "ssc_denovo",
            rst_ref=f"{_GS_RST}:37",
            expectation="de Novo gene sets are generated for ssc_denovo",
        )

    def test_raises_when_dataset_missing(self):
        resp = _FakeResponse(
            200,
            json_body=[{"datasetId": "denovo_example"}],
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_denovo_gene_sets_for_dataset(
                resp, "ssc_denovo",
                rst_ref=f"{_GS_RST}:37",
                expectation="de Novo gene sets are generated for ssc_denovo",
            )
        message = str(exc_info.value)
        assert f"{_GS_RST}:37" in message
        assert "ssc_denovo" in message
        assert "denovo_example" in message
        assert "Triage" in message

    def test_raises_on_http_error(self):
        resp = _FakeResponse(500, text="Internal Server Error")
        with pytest.raises(AssertionError) as exc_info:
            assert_denovo_gene_sets_for_dataset(
                resp, "ssc_denovo",
                rst_ref=f"{_GS_RST}:37",
                expectation="de Novo gene sets are generated for ssc_denovo",
            )
        assert "500" in str(exc_info.value)


_EN_RST = "getting_started_with_enrichment.rst"

# A realistic enrichment models payload for a de Novo study: the single
# samocha background the guide says is configured by default, plus a counting
# model and the defaults the SPA uses to seed the form.
_ENRICHMENT_MODELS_BODY = {
    "background": [
        {
            "id": "enrichment/samocha_background",
            "name": "Samocha's enrichment background model",
            "type": "samocha_enrichment_background",
        },
    ],
    "counting": [
        {"id": "enrichment_events_counting", "name": "Counting events"},
    ],
    "defaultBackground": "enrichment/samocha_background",
    "defaultCounting": "enrichment_events_counting",
}


class TestAssertEnrichmentModels:
    def test_passes_when_tool_enabled(self):
        resp = _FakeResponse(200, json_body=_ENRICHMENT_MODELS_BODY)
        assert_enrichment_models(
            resp,
            rst_ref=f"{_EN_RST}:4",
            expectation="the Enrichment tool is enabled for ssc_denovo",
        )

    def test_raises_when_tool_not_enabled(self):
        resp = _FakeResponse(
            200,
            json_body={"background": [], "counting": []},
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_enrichment_models(
                resp,
                rst_ref=f"{_EN_RST}:4",
                expectation="the Enrichment tool is enabled for ssc_denovo",
            )
        message = str(exc_info.value)
        assert f"{_EN_RST}:4" in message
        assert "Triage" in message

    def test_passes_when_background_ids_match(self):
        resp = _FakeResponse(200, json_body=_ENRICHMENT_MODELS_BODY)
        assert_enrichment_models(
            resp,
            require_background_ids=["enrichment/samocha_background"],
            rst_ref=f"{_EN_RST}:20",
            expectation="only the samocha background is configured by default",
        )

    def test_raises_when_extra_background_present(self):
        body = {
            **_ENRICHMENT_MODELS_BODY,
            "background": [
                {"id": "enrichment/samocha_background"},
                {"id": "enrichment/coding_len_background"},
            ],
        }
        resp = _FakeResponse(200, json_body=body)
        with pytest.raises(AssertionError) as exc_info:
            assert_enrichment_models(
                resp,
                require_background_ids=["enrichment/samocha_background"],
                rst_ref=f"{_EN_RST}:20",
                expectation=(
                    "only the samocha background is configured by default"
                ),
            )
        message = str(exc_info.value)
        assert f"{_EN_RST}:20" in message
        assert "enrichment/coding_len_background" in message
        assert "Triage" in message

    def test_raises_on_http_error(self):
        resp = _FakeResponse(500, text="Internal Server Error")
        with pytest.raises(AssertionError) as exc_info:
            assert_enrichment_models(
                resp,
                rst_ref=f"{_EN_RST}:4",
                expectation="the Enrichment tool is enabled for ssc_denovo",
            )
        assert "500" in str(exc_info.value)


# A realistic /enrichment/test response for a CHD8 query against ssc_denovo:
# one record per person-set value. The affected/autism record carries the 3
# de-novo LGDs that overlap CHD8 (frame-shift + nonsense + splice-site);
# missense/synonymous overlap 0; the unaffected record overlaps nothing.
_ENRICHMENT_TEST_BODY = {
    "desc": "CHD8",
    "result": [
        {
            "selector": "autism",
            "peopleGroupId": "phenotype",
            "peopleGroupValue": "autism",
            "childrenStats": {"M": 100, "F": 20},
            "LGDs": {"all": {"name": "all", "count": 8, "overlapped": 3,
                             "expected": 0.5, "pvalue": 0.001}},
            "missense": {"all": {"name": "all", "count": 12, "overlapped": 0,
                                 "expected": 1.0, "pvalue": 1.0}},
            "synonymous": {"all": {"name": "all", "count": 9, "overlapped": 0,
                                   "expected": 1.0, "pvalue": 1.0}},
        },
        {
            "selector": "unaffected",
            "peopleGroupId": "phenotype",
            "peopleGroupValue": "unaffected",
            "childrenStats": {"M": 50, "F": 60},
            "LGDs": {"all": {"name": "all", "count": 4, "overlapped": 0,
                             "expected": 0.4, "pvalue": 1.0}},
            "missense": {"all": {"name": "all", "count": 7, "overlapped": 0,
                                 "expected": 0.9, "pvalue": 1.0}},
            "synonymous": {"all": {"name": "all", "count": 6, "overlapped": 0,
                                   "expected": 0.9, "pvalue": 1.0}},
        },
    ],
}


class TestAssertEnrichmentTestResult:
    def test_passes_when_result_present(self):
        resp = _FakeResponse(
            200,
            json_body={
                "desc": "CHD8",
                "result": [{"selector": "autism", "datasetId": "ssc_denovo"}],
            },
        )
        assert_enrichment_test_result(
            resp,
            rst_ref=f"{_EN_RST}:26",
            expectation="the user can run enrichment tests and get results",
        )

    def test_raises_when_result_empty(self):
        resp = _FakeResponse(200, json_body={"desc": "CHD8", "result": []})
        with pytest.raises(AssertionError) as exc_info:
            assert_enrichment_test_result(
                resp,
                rst_ref=f"{_EN_RST}:26",
                expectation="the user can run enrichment tests and get results",
            )
        message = str(exc_info.value)
        assert f"{_EN_RST}:26" in message
        assert "Triage" in message

    def test_raises_when_result_absent(self):
        resp = _FakeResponse(200, json_body={"desc": "CHD8"})
        with pytest.raises(AssertionError) as exc_info:
            assert_enrichment_test_result(
                resp,
                rst_ref=f"{_EN_RST}:26",
                expectation="the user can run enrichment tests and get results",
            )
        assert "absent" in str(exc_info.value)

    def test_raises_on_http_error(self):
        resp = _FakeResponse(400, text="Bad Request")
        with pytest.raises(AssertionError) as exc_info:
            assert_enrichment_test_result(
                resp,
                rst_ref=f"{_EN_RST}:26",
                expectation="the user can run enrichment tests and get results",
            )
        assert "400" in str(exc_info.value)

    def test_passes_when_observed_positive(self):
        resp = _FakeResponse(200, json_body=_ENRICHMENT_TEST_BODY)
        assert_enrichment_test_result(
            resp,
            rst_ref=f"{_EN_RST}:26",
            expectation="the user can run enrichment tests and get results",
            require_observed=True,
        )

    def test_raises_when_observed_zero(self):
        body = {
            "desc": "CHD8",
            "result": [
                {
                    "selector": "autism",
                    "LGDs": {"all": {"overlapped": 0}},
                    "missense": {"all": {"overlapped": 0}},
                    "synonymous": {"all": {"overlapped": 0}},
                },
            ],
        }
        resp = _FakeResponse(200, json_body=body)
        with pytest.raises(AssertionError) as exc_info:
            assert_enrichment_test_result(
                resp,
                rst_ref=f"{_EN_RST}:26",
                expectation="the user can run enrichment tests",
                require_observed=True,
            )
        message = str(exc_info.value)
        assert f"{_EN_RST}:26" in message
        assert "observed" in message.lower()
        assert "Triage" in message

    def test_passes_when_lgd_overlap_matches(self):
        resp = _FakeResponse(200, json_body=_ENRICHMENT_TEST_BODY)
        assert_enrichment_test_result(
            resp,
            rst_ref=f"{_EN_RST}:26",
            expectation="CHD8 shows the canonical 3 de-novo LGDs",
            require_observed=True,
            expect_lgd_overlapped=3,
        )

    def test_raises_when_lgd_overlap_drifts(self):
        resp = _FakeResponse(200, json_body=_ENRICHMENT_TEST_BODY)
        with pytest.raises(AssertionError) as exc_info:
            assert_enrichment_test_result(
                resp,
                rst_ref=f"{_EN_RST}:26",
                expectation="CHD8 shows the canonical 3 de-novo LGDs",
                expect_lgd_overlapped=5,
            )
        message = str(exc_info.value)
        assert f"{_EN_RST}:26" in message
        assert "3" in message and "5" in message


_GP_RST = "getting_started_with_gene_profiles.rst"


class TestAssertGeneProfilesConfigured:
    def test_passes_with_nonempty_config(self):
        resp = _FakeResponse(
            200, json_body={"defaultDataset": "ssc_denovo", "order": []},
        )
        assert_gene_profiles_configured(
            resp, default_dataset="ssc_denovo",
            rst_ref=f"{_GP_RST}:142",
            expectation="the home page shows the Gene Profiles tool",
        )

    def test_passes_without_default_dataset_check(self):
        resp = _FakeResponse(200, json_body={"defaultDataset": "anything"})
        assert_gene_profiles_configured(
            resp,
            rst_ref=f"{_GP_RST}:142",
            expectation="the Gene Profiles tool is enabled",
        )

    def test_raises_on_empty_config(self):
        # 200 + {} is the tool-not-enabled case — must NOT pass.
        resp = _FakeResponse(200, json_body={})
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_profiles_configured(
                resp,
                rst_ref=f"{_GP_RST}:142",
                expectation="the home page shows the Gene Profiles tool",
            )
        message = str(exc_info.value)
        assert f"{_GP_RST}:142" in message
        assert "not enabled" in message.lower()

    def test_raises_on_default_dataset_mismatch(self):
        resp = _FakeResponse(200, json_body={"defaultDataset": "other"})
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_profiles_configured(
                resp, default_dataset="ssc_denovo",
                rst_ref=f"{_GP_RST}:142",
                expectation="the Gene Profiles tool uses ssc_denovo",
            )
        message = str(exc_info.value)
        assert "ssc_denovo" in message
        assert "other" in message

    def test_raises_on_http_error(self):
        resp = _FakeResponse(500, text="Internal Server Error")
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_profiles_configured(
                resp,
                rst_ref=f"{_GP_RST}:142",
                expectation="the Gene Profiles tool is enabled",
            )
        assert "HTTP 500" in str(exc_info.value)


class TestAssertGeneProfileTableRows:
    def test_passes_with_rows_and_required_symbol(self):
        resp = _FakeResponse(200, json_body=[
            {"geneSymbol": "CHD8"}, {"geneSymbol": "ANK2"},
        ])
        assert_gene_profile_table_rows(
            resp, min_count=2, require_symbols=["CHD8"],
            rst_ref=f"{_GP_RST}:147",
            expectation="the All Genes table lists gene profiles",
        )

    def test_raises_when_too_few_rows(self):
        resp = _FakeResponse(200, json_body=[{"geneSymbol": "CHD8"}])
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_profile_table_rows(
                resp, min_count=10,
                rst_ref=f"{_GP_RST}:147",
                expectation="the All Genes table lists the prebuilt genes",
            )
        message = str(exc_info.value)
        assert f"{_GP_RST}:147" in message
        assert "10" in message

    def test_raises_when_required_symbol_missing(self):
        resp = _FakeResponse(200, json_body=[
            {"geneSymbol": "ANK2"}, {"geneSymbol": "DSCAM"},
        ])
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_profile_table_rows(
                resp, min_count=1, require_symbols=["CHD8"],
                rst_ref=f"{_GP_RST}:147",
                expectation="CHD8 is in the gene profiles table",
            )
        assert "CHD8" in str(exc_info.value)

    def test_raises_on_http_error(self):
        resp = _FakeResponse(503, text="Service Unavailable")
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_profile_table_rows(
                resp, min_count=1,
                rst_ref=f"{_GP_RST}:147",
                expectation="the All Genes table lists gene profiles",
            )
        assert "HTTP 503" in str(exc_info.value)


class TestAssertGeneProfileForGene:
    def test_passes_with_matching_gene(self):
        resp = _FakeResponse(200, json_body={
            "geneSymbol": "CHD8", "geneSets": [], "geneScores": [],
        })
        assert_gene_profile_for_gene(
            resp, "CHD8",
            rst_ref=f"{_GP_RST}:156",
            expectation="the CHD8 Gene Profile page opens",
        )

    def test_raises_on_404(self):
        # The endpoint 404s when the gene has no generated profile.
        resp = _FakeResponse(404, text="Not Found")
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_profile_for_gene(
                resp, "CHD8",
                rst_ref=f"{_GP_RST}:156",
                expectation="the CHD8 Gene Profile page opens",
            )
        message = str(exc_info.value)
        assert f"{_GP_RST}:156" in message
        assert "HTTP 404" in message

    def test_raises_on_wrong_gene(self):
        resp = _FakeResponse(200, json_body={"geneSymbol": "ANK2"})
        with pytest.raises(AssertionError) as exc_info:
            assert_gene_profile_for_gene(
                resp, "CHD8",
                rst_ref=f"{_GP_RST}:156",
                expectation="the CHD8 Gene Profile page opens",
            )
        assert "CHD8" in str(exc_info.value)


_PI_RST = "getting_started_with_python_interface.rst"


class TestAssertPythonSnippetOutput:
    def test_passes_on_matching_value(self):
        # No exception when the captured value equals the documented one.
        assert_python_snippet_output(
            {"synonymous_count": 4}, "synonymous_count", 4,
            rst_ref=f"{_PI_RST}:90",
            expectation="synonymous query yields 4",
        )

    def test_passes_on_matching_list_and_dict(self):
        values = {
            "ids": ["a", "b", "c"],
            "instruments": {"basic_medical": 4, "iq": 3},
        }
        assert_python_snippet_output(
            values, "ids", ["a", "b", "c"],
            rst_ref=f"{_PI_RST}:29", expectation="ids match",
        )
        # dict equality is order-independent (json round-trips can reorder).
        assert_python_snippet_output(
            values, "instruments", {"iq": 3, "basic_medical": 4},
            rst_ref=f"{_PI_RST}:134", expectation="instruments match",
        )

    def test_raises_on_value_mismatch(self):
        with pytest.raises(AssertionError) as exc_info:
            assert_python_snippet_output(
                {"synonymous_count": 5}, "synonymous_count", 4,
                rst_ref=f"{_PI_RST}:90",
                expectation="synonymous query yields 4",
            )
        message = str(exc_info.value)
        assert f"{_PI_RST}:90" in message
        assert "synonymous query yields 4" in message
        # both the expected and the actual value are surfaced
        assert "4" in message
        assert "5" in message
        # mismatch triage points at guide-output / API drift
        assert "update the guide" in message

    def test_raises_on_missing_key_when_driver_succeeded(self):
        # Driver exited 0 but never emitted the key — the marker key drifted.
        with pytest.raises(AssertionError) as exc_info:
            assert_python_snippet_output(
                {}, "synonymous_count", 4,
                rst_ref=f"{_PI_RST}:90",
                expectation="synonymous query yields 4",
                after_command=_ok_result(),
            )
        message = str(exc_info.value)
        assert "marker key" in message
        assert "not produced" in message

    def test_raises_on_missing_key_when_driver_failed(self):
        # Driver exited non-zero — the snippet output was never produced; the
        # message redirects to the driver failure and surfaces its stderr.
        failed = SimpleNamespace(
            returncode=1,
            args=["python", "driver.py"],
            stdout=b"",
            stderr=b"ModuleNotFoundError: No module named 'dae'\n",
        )
        with pytest.raises(AssertionError) as exc_info:
            assert_python_snippet_output(
                {}, "genotype_data_ids", ["example_dataset"],
                rst_ref=f"{_PI_RST}:29",
                expectation="study ids listed",
                after_command=failed,
            )
        message = str(exc_info.value)
        assert "exit code 1" in message
        # the driver's traceback tail is surfaced for triage
        assert "No module named 'dae'" in message
        assert "Fix that failure first" in message
