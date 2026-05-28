"""Guide-claim tests for getting_started_with_preview_columns.rst.

The preview-columns section tells the user to edit the
``example_dataset`` config and, in the ``genotype_browser`` section:

1. redefine the existing ``frequency`` column group to include the
   gnomAD frequency ``gnomad_v4_genome_ALL_af`` (the attribute the
   annotation guide added), and define a new ``clinvar`` column group
   carrying the ClinVar attributes ``CLNSIG`` + ``CLNDN`` — then add
   ``clinvar`` to ``preview_columns_ext`` so it shows in the preview
   table;
2. define two phenotype columns (``prb_verbal_iq`` /
   ``prb_non_verbal_iq``, sourcing the ``iq.*`` measures of the
   ``mini_pheno`` study attached in the phenotype guide), group them as
   ``proband_iq``, and add that group to ``preview_columns_ext`` too.

The config edit lives in the session-scoped ``preview_columns_instance``
fixture (conftest.py); ``wgpf_server`` depends on it, so the single
shared server serves the dataset with the extended preview layout.
Strict mode (#871): the fixture only does what the guide tells the user
to do — the one-block yaml edit (the guide's final code-block, which is
a strict superset of its first edit).

The resolved preview layout surfaces through the single-dataset
description endpoint at
``data.genotype_browser_config.table_columns`` — the same list the SPA
renders as the preview table. Each test maps to one discrete prose
claim; ``rst_ref`` points at the line in the guide source so a failure
localizes the drift.
"""

from docs_e2e.guide_assertions import assert_preview_table_column_group

RST = "getting_started_with_preview_columns.rst"


def _description(wgpf_server):
    return wgpf_server.client.get("/api/v3/datasets/example_dataset")


class TestGenotypeColumnConfig:
    """RST lines 5-95: redefining ``frequency`` and adding the ``clinvar``
    column group surfaces the annotation attributes in the preview
    table."""

    def test_clinvar_column_group_in_preview_table(self, wgpf_server):
        # RST lines 77-78: adding `clinvar` to preview_columns_ext makes
        # the new column group appear in the preview table.
        assert_preview_table_column_group(
            _description(wgpf_server), "ClinVar",
            rst_ref=f"{RST}:78",
            expectation=(
                "the new `clinvar` column group is added to the preview "
                "table"
            ),
        )

    def test_clinvar_group_has_clnsig_and_clndn(self, wgpf_server):
        # RST lines 73-75: the `clinvar` group contains the ClinVar
        # annotation attributes CLNSIG and CLNDN.
        assert_preview_table_column_group(
            _description(wgpf_server), "ClinVar",
            expected_sources=["CLNSIG", "CLNDN"],
            rst_ref=f"{RST}:73",
            expectation=(
                "the `clinvar` column group contains the CLNSIG and CLNDN "
                "annotation attributes"
            ),
        )

    def test_frequency_group_includes_gnomad(self, wgpf_server):
        # RST lines 69-71: the redefined `frequency` group includes the
        # gnomAD frequency. (allele_freq may also be present; only the
        # gnomAD attribute is asserted — that is the guide's claim.)
        assert_preview_table_column_group(
            _description(wgpf_server), "frequency",
            expected_sources=["gnomad_v4_genome_ALL_af"],
            rst_ref=f"{RST}:69",
            expectation=(
                "the existing `frequency` column group is redefined to "
                "include the gnomAD frequency gnomad_v4_genome_ALL_af"
            ),
        )


class TestPhenotypeColumnConfig:
    """RST lines 98-200: defining phenotype columns and grouping them as
    ``proband_iq`` surfaces the pheno measures in the preview table."""

    def test_proband_iq_column_group_in_preview_table(self, wgpf_server):
        # RST lines 192-193: the new column group `proband_iq` appears in
        # the preview table after adding it to preview_columns_ext.
        assert_preview_table_column_group(
            _description(wgpf_server), "Proband IQ",
            rst_ref=f"{RST}:193",
            expectation=(
                "the new `proband_iq` column group appears in the preview "
                "table"
            ),
        )

    def test_proband_iq_group_has_both_iq_measures(self, wgpf_server):
        # RST lines 164-178: the `proband_iq` group carries the two
        # phenotype columns — sourcing iq.verbal_iq / iq.non_verbal_iq,
        # displayed as `Verbal IQ` / `Non-Verbal IQ`.
        assert_preview_table_column_group(
            _description(wgpf_server), "Proband IQ",
            expected_sources=["iq.verbal_iq", "iq.non_verbal_iq"],
            expected_column_names=["Verbal IQ", "Non-Verbal IQ"],
            rst_ref=f"{RST}:164",
            expectation=(
                "the `proband_iq` column group carries the Verbal IQ and "
                "Non-Verbal IQ proband measures (iq.verbal_iq, "
                "iq.non_verbal_iq)"
            ),
        )
