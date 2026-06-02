"""Guide-claim tests for example_denovo_import.rst.

The de novo import sub-guide imports a separate large study,
``ssc_denovo`` (255K real SSC de novo variants), into the same
``minimal_instance`` the main guide built, then edits the study config
to add preview columns. It walks the user through:

1. preprocessing the supplementary data with two awk pipelines into a
   pedigree file (``ssc_denovo.ped``) and a de novo variants file
   (``ssc_denovo.tsv``);
2. configuring a local GRR cache (``.grr_definition.yaml``) so the
   255K-variant annotation's demand-pulled resources persist locally;
3. importing the study with ``import_genotypes -v -j 10`` — annotated
   with the gnomAD + ClinVar scores the instance config defines;
4. seeing ``ssc_denovo`` on the Home Page and querying it in the
   Genotype Browser;
5. editing the study config's ``genotype_browser`` section to surface
   the ``frequency`` (incl. gnomAD) and ``ClinVar`` column groups in the
   preview table.

The imports + config edit live in the session-scoped ``denovo_instance``
fixture (conftest.py); ``wgpf_server`` depends on it, so the single
shared server serves the ssc_denovo-enabled instance. Strict mode
(#871): the fixture only does what the guide tells the user to do — the
awk pipelines, the GRR cache + import CLIs, and the study yaml edit.

Each test maps to one discrete prose claim. ``rst_ref`` points at the
line in the guide source so a failure localizes the drift.
"""

from docs_e2e.guide_assertions import (
    assert_command_succeeds,
    assert_dataset_visible,
    assert_file_created,
    assert_preview_table_column_group,
    assert_query_returned_variants,
)

RST = "example_denovo_import.rst"


def _description(wgpf_server):
    return wgpf_server.client.get("/api/v3/datasets/ssc_denovo")


class TestPreprocessFamilyData:
    """RST lines 109-128: the Family-Data awk reads
    ``Supplementary_Data_1.tsv.gz`` and produces ``ssc_denovo.ped``."""

    def test_ped_awk_command_succeeds(self, denovo_instance):
        # RST lines 111-124: the awk pipeline that builds the pedigree.
        assert_command_succeeds(
            denovo_instance.ped_awk,
            rst_ref=f"{RST}:124",
            expectation=(
                "the Family-Data awk pipeline over Supplementary_Data_1."
                "tsv.gz succeeds"
            ),
        )

    def test_ssc_denovo_ped_created(self, denovo_instance):
        # RST line 127: the script produces the pedigree file
        # ssc_denovo.ped.
        path = (
            denovo_instance.clone_path
            / "example_imports" / "denovo_and_cnv_import" / "ssc_denovo.ped"
        )
        assert_file_created(
            path,
            rst_ref=f"{RST}:127",
            expectation=(
                "the awk script produces the pedigree file ssc_denovo.ped"
            ),
            after_command=denovo_instance.ped_awk,
        )


class TestPreprocessVariants:
    """RST lines 165-186: the variant awk reads
    ``Supplementary_Data_2.tsv.gz`` and produces ``ssc_denovo.tsv``."""

    def test_tsv_awk_command_succeeds(self, denovo_instance):
        # RST lines 170-178: the awk pipeline that builds the variants
        # file.
        assert_command_succeeds(
            denovo_instance.tsv_awk,
            rst_ref=f"{RST}:181",
            expectation=(
                "the variant awk pipeline over Supplementary_Data_2.tsv.gz "
                "succeeds"
            ),
        )

    def test_ssc_denovo_tsv_created(self, denovo_instance):
        # RST line 181-184: the script produces the de novo variants file
        # ssc_denovo.tsv.
        path = (
            denovo_instance.clone_path
            / "example_imports" / "denovo_and_cnv_import" / "ssc_denovo.tsv"
        )
        assert_file_created(
            path,
            rst_ref=f"{RST}:184",
            expectation=(
                "the awk script produces the de novo variants file "
                "ssc_denovo.tsv"
            ),
            after_command=denovo_instance.tsv_awk,
        )


class TestCachingGRR:
    """RST lines 205-235: the "Caching GRR" step configures a local GRR
    cache and pre-downloads the instance's annotation resources with
    ``grr_cache_repo -i minimal_instance/gpf_instance.yaml``."""

    def test_grr_cache_repo_command_succeeds(self, denovo_instance):
        # RST line 225: grr_cache_repo -i minimal_instance/gpf_instance.yaml
        # caches the instance annotation resources. The CLI ships in
        # gain-core (a transitive dep of the gpf-web conda package), so it
        # is on PATH after `mamba install gpf-web` — a drift here would be
        # the #876 "command not found" regression resurfacing.
        assert_command_succeeds(
            denovo_instance.grr_cache,
            rst_ref=f"{RST}:225",
            expectation=(
                "grr_cache_repo -i minimal_instance/gpf_instance.yaml "
                "caches the instance annotation resources"
            ),
        )


class TestSscDenovoImport:
    """RST lines 250-319: importing the ssc_denovo study and seeing it on
    the Home Page / querying it in the Genotype Browser."""

    def test_import_genotypes_command_succeeds(self, denovo_instance):
        # RST line 279: time import_genotypes -v -j 10 .../ssc_denovo.yaml.
        # The guide imports 255K variants; the suite caps the input to the
        # first 50 (conftest, #876 carve-out) but runs this command verbatim.
        assert_command_succeeds(
            denovo_instance.ssc_denovo_import,
            rst_ref=f"{RST}:279",
            expectation=(
                "import_genotypes -v -j 10 example_imports/"
                "denovo_and_cnv_import/ssc_denovo.yaml succeeds"
            ),
        )

    def test_study_yaml_created(self, denovo_instance):
        # RST line 307 (+ config path RST line 334): the import produces
        # the study config under studies/ssc_denovo/ssc_denovo.yaml.
        path = (
            denovo_instance.instance_dir
            / "studies" / "ssc_denovo" / "ssc_denovo.yaml"
        )
        assert_file_created(
            path,
            rst_ref=f"{RST}:307",
            expectation=(
                "minimal_instance/studies/ssc_denovo/ssc_denovo.yaml is "
                "created after the ssc_denovo import"
            ),
            after_command=denovo_instance.ssc_denovo_import,
        )

    def test_ssc_denovo_visible_on_home_page(self, wgpf_server):
        # RST lines 307-308: the Home page shows the new study ssc_denovo.
        resp = wgpf_server.client.get("/api/v3/datasets/visible")
        assert_dataset_visible(
            resp, "ssc_denovo",
            rst_ref=f"{RST}:308",
            expectation=(
                "in the Home page of the GPF instance, we should have the "
                "new study `ssc_denovo`"
            ),
        )

    def test_genotype_browser_returns_variants(self, wgpf_server):
        # RST lines 314-315: following the study's Genotype Browser tab
        # lets you query the imported variants.
        resp = wgpf_server.client.post(
            "/api/v3/genotype_browser/query",
            json={"datasetId": "ssc_denovo"},
        )
        # min_count=10: the import is capped to the CHD8 +/- 250 kb window
        # (conftest _DENOVO_CHD8_REGION, #876 carve-out) = 50 chr14 variants,
        # so requiring >=10 back proves the import substantively worked rather
        # than one row squeaking through — without coupling to an exact
        # post-import count (paging / per-allele fan-out).
        assert_query_returned_variants(
            resp,
            min_count=10,
            rst_ref=f"{RST}:314",
            expectation=(
                "the Genotype Browser of the ssc_denovo study returns the "
                "imported variants"
            ),
        )


class TestPreviewColumnConfig:
    """RST lines 322-367: editing the ssc_denovo study config's
    ``genotype_browser`` section surfaces the gnomAD + ClinVar column
    groups in the preview table."""

    def test_frequency_group_includes_gnomad(self, wgpf_server):
        # RST lines 342-346 + 366-367: the `frequency` column group is
        # defined with the gnomAD frequency, surfacing in the preview
        # table.
        assert_preview_table_column_group(
            _description(wgpf_server), "frequency",
            expected_sources=["gnomad_v4_genome_ALL_af"],
            rst_ref=f"{RST}:367",
            expectation=(
                "the preview table contains the `frequency` column group "
                "with the GnomAD genomic score"
            ),
        )

    def test_clinvar_group_in_preview_table(self, wgpf_server):
        # RST lines 348-355 + 366-367: adding `clinvar` to
        # preview_columns_ext surfaces the ClinVar column group with the
        # CLNSIG + CLNDN attributes in the preview table.
        assert_preview_table_column_group(
            _description(wgpf_server), "ClinVar",
            expected_sources=["CLNSIG", "CLNDN"],
            rst_ref=f"{RST}:367",
            expectation=(
                "the preview table contains the `ClinVar` column group with "
                "the CLNSIG + CLNDN ClinVar scores"
            ),
        )
