"""Guide-claim tests for example_cnv_import.rst.

The CNV import sub-guide imports a CNV study, ``ssc_cnv`` (SSC CNV
variants from the Yoon et al. paper), into the same ``minimal_instance``
the earlier guides built, reusing the ``ssc_denovo.ped`` pedigree. It
walks the user through:

1. preprocessing ``Supplementary_Data_4.tsv.gz`` with an awk pipeline
   that filters the SSC collection into a CNV variants file
   (``ssc_cnv.tsv``);
2. importing the study with ``import_genotypes -v -j 1``;
3. seeing ``ssc_cnv`` on the Home Page and querying its CNV variants in
   the Genotype Browser.

The awk + import live in the session-scoped ``cnv_instance`` fixture
(conftest.py); ``wgpf_server`` depends on it, so the single shared server
serves the ssc_cnv-enabled instance. Strict mode (#871): the fixture only
does what the guide tells the user to do — the awk pipeline and the import
CLI. The single carve-out is the ``_CNV_VARIANT_CAP`` truncation of the
awk output (#877, mirroring the #876 denovo cap).

Each test maps to one discrete prose claim. ``rst_ref`` points at the
line in the guide source so a failure localizes the drift.
"""

from docs_e2e.guide_assertions import (
    assert_command_succeeds,
    assert_dataset_visible,
    assert_file_created,
    assert_query_returned_variants,
)

RST = "example_cnv_import.rst"


class TestPreprocessCnv:
    """RST lines 71-90: the SSC-filter awk reads
    ``Supplementary_Data_4.tsv.gz`` and produces ``ssc_cnv.tsv``."""

    def test_cnv_awk_command_succeeds(self, cnv_instance):
        # RST lines 76-83: the awk pipeline that filters the SSC
        # collection into the CNV variants file.
        assert_command_succeeds(
            cnv_instance.cnv_awk,
            rst_ref=f"{RST}:83",
            expectation=(
                "the SSC-filter awk pipeline over "
                "Supplementary_Data_4.tsv.gz succeeds"
            ),
        )

    def test_ssc_cnv_tsv_created(self, cnv_instance):
        # RST lines 85-90: the script produces the CNV variants file
        # ssc_cnv.tsv.
        path = (
            cnv_instance.clone_path
            / "example_imports" / "denovo_and_cnv_import" / "ssc_cnv.tsv"
        )
        assert_file_created(
            path,
            rst_ref=f"{RST}:85",
            expectation=(
                "the awk script produces the CNV variants file "
                "ssc_cnv.tsv"
            ),
            after_command=cnv_instance.cnv_awk,
        )


class TestSscCnvImport:
    """RST lines 99-143: importing the ssc_cnv study and seeing it on the
    Home Page / querying it in the Genotype Browser."""

    def test_import_genotypes_command_succeeds(self, cnv_instance):
        # RST line 125: time import_genotypes -v -j 1 .../ssc_cnv.yaml.
        # The guide imports the full SSC CNV set; the suite caps the input
        # to the first 20 (conftest, #877 carve-out) but runs this command
        # verbatim.
        assert_command_succeeds(
            cnv_instance.ssc_cnv_import,
            rst_ref=f"{RST}:125",
            expectation=(
                "import_genotypes -v -j 1 example_imports/"
                "denovo_and_cnv_import/ssc_cnv.yaml succeeds"
            ),
        )

    def test_study_yaml_created(self, cnv_instance):
        # RST lines 134-135: the import produces the study config under
        # studies/ssc_cnv/ssc_cnv.yaml.
        path = (
            cnv_instance.instance_dir
            / "studies" / "ssc_cnv" / "ssc_cnv.yaml"
        )
        assert_file_created(
            path,
            rst_ref=f"{RST}:135",
            expectation=(
                "minimal_instance/studies/ssc_cnv/ssc_cnv.yaml is "
                "created after the ssc_cnv import"
            ),
            after_command=cnv_instance.ssc_cnv_import,
        )

    def test_ssc_cnv_visible_on_home_page(self, wgpf_server):
        # RST lines 134-135: the Home page shows the new study ssc_cnv.
        resp = wgpf_server.client.get("/api/v3/datasets/visible")
        assert_dataset_visible(
            resp, "ssc_cnv",
            rst_ref=f"{RST}:135",
            expectation=(
                "in the Home page of the GPF instance, we should have "
                "the new study `ssc_cnv`"
            ),
        )

    def test_genotype_browser_returns_cnv_variants(self, wgpf_server):
        # RST lines 141-143: following the study's Genotype Browser tab
        # lets you query the imported CNV variants.
        resp = wgpf_server.client.post(
            "/api/v3/genotype_browser/query",
            json={"datasetId": "ssc_cnv"},
        )
        # min_count=5: the import is capped to the guide's first 20 CNV
        # variants (conftest, #877 carve-out), so requiring >=5 back proves
        # the import substantively worked rather than one row squeaking
        # through — without coupling to an exact post-import count.
        assert_query_returned_variants(
            resp,
            min_count=5,
            rst_ref=f"{RST}:143",
            expectation=(
                "the Genotype Browser of the ssc_cnv study returns the "
                "imported CNV variants"
            ),
        )
