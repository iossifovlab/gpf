"""Guide-claim tests for example_pheno_import.rst.

The phenotype-import sub-guide imports a real SSC proband phenotype study,
``ssc_pheno`` (from the Iossifov et al. 2014 Nature paper Supplementary
Table 1), into the same ``minimal_instance`` the earlier guides built, and
then attaches it to the ``ssc_denovo`` genotype study. It walks the user
through:

1. preprocessing ``Supplementary_Table_1.tsv.gz`` with two awk pipelines —
   one building the pedigree file ``ssc_pheno.ped`` (SSC families), one
   building the instrument file ``proband_measures.csv`` (six proband
   measures);
2. importing the study with ``import_phenotypes .../ssc_pheno.yaml``;
3. seeing ``ssc_pheno`` on the Home Page and browsing its instrument /
   measures in the Phenotype Browser;
4. adding ``phenotype_data: ssc_pheno`` to the ``ssc_denovo`` study config,
   which enables the Phenotype Browser + Phenotype Tool tabs for that
   genotype study.

The awk pipelines, the ``import_phenotypes`` call, and the ssc_denovo
config edit live in the session-scoped ``pheno_import_instance`` fixture
(conftest.py); ``wgpf_server`` depends on it, so the single shared server
serves the ssc_pheno-enabled instance. Strict mode (#871): the fixture
only does what the guide tells the user to do — the two awk pipelines, the
CLI import, and the one-line yaml edit. The single carve-out is the
``_PHENO_PROBAND_CAP`` truncation of the awk-produced proband_measures.csv
(#878, mirroring the #876 denovo / #877 cnv caps): ``wgpf run`` builds the
phenotype browser (per-measure figures + regressions) synchronously on
startup, and the full SSC table (~2.5K probands x 6 measures) does not
finish that build inside the shared server's readiness window — so the
import is capped to the guide's first N probands while the awk pipelines
and ``import_phenotypes`` still run verbatim (see ``_PHENO_PROBAND_CAP`` in
conftest.py).

Each test maps to one discrete prose claim. ``rst_ref`` points at the line
in the guide source so a failure localizes the drift.
"""

from docs_e2e.guide_assertions import (
    assert_command_succeeds,
    assert_dataset_description_flag,
    assert_dataset_visible,
    assert_file_created,
    assert_pheno_instruments_available,
    assert_pheno_measures_present,
)

RST = "example_pheno_import.rst"

# The instrument import_phenotypes derives from the bare
# ``proband_measures.csv`` instrument file (collect_instruments names it
# from ``match.name.split(".")[0]`` when no explicit instrument name is
# given — see core/gpf/pheno/pheno_import.py).
PHENO_INSTRUMENT = "proband_measures"


class TestPreprocessFamilyData:
    """RST lines 70-103: the Family-Data awk reads
    ``Supplementary_Table_1.tsv.gz`` and produces the pedigree file
    ``ssc_pheno.ped``."""

    def test_ssc_pheno_ped_awk_command_succeeds(self, pheno_import_instance):
        # RST lines 72-88: the awk pipeline that builds the pedigree from
        # the SSC-collection families.
        assert_command_succeeds(
            pheno_import_instance.pheno_ped_awk,
            rst_ref=f"{RST}:88",
            expectation=(
                "the Family-Data awk pipeline over "
                "Supplementary_Table_1.tsv.gz succeeds"
            ),
        )

    def test_ssc_pheno_ped_created(self, pheno_import_instance):
        # RST lines 90-91: the script produces the pedigree file
        # ssc_pheno.ped.
        path = (
            pheno_import_instance.clone_path
            / "example_imports" / "pheno_import" / "ssc_pheno.ped"
        )
        assert_file_created(
            path,
            rst_ref=f"{RST}:91",
            expectation=(
                "the awk script produces the pedigree file ssc_pheno.ped"
            ),
            after_command=pheno_import_instance.pheno_ped_awk,
        )


class TestPreprocessMeasures:
    """RST lines 105-178: the phenotype-measures awk reads the same table
    and produces the instrument file ``proband_measures.csv``."""

    def test_proband_measures_awk_command_succeeds(
            self, pheno_import_instance):
        # RST lines 146-153: the awk pipeline that extracts the six
        # proband measures into the instrument file.
        assert_command_succeeds(
            pheno_import_instance.pheno_measures_awk,
            rst_ref=f"{RST}:153",
            expectation=(
                "the phenotype-measures awk pipeline over "
                "Supplementary_Table_1.tsv.gz succeeds"
            ),
        )

    def test_proband_measures_csv_created(self, pheno_import_instance):
        # RST lines 156-157: the script produces the instrument file
        # proband_measures.csv.
        path = (
            pheno_import_instance.clone_path
            / "example_imports" / "pheno_import" / "proband_measures.csv"
        )
        assert_file_created(
            path,
            rst_ref=f"{RST}:156",
            expectation=(
                "the awk script produces the instrument file "
                "proband_measures.csv"
            ),
            after_command=pheno_import_instance.pheno_measures_awk,
        )


class TestSscPhenoImport:
    """RST lines 181-210: importing the ssc_pheno study and seeing it on
    the Home Page / browsing it in the Phenotype Browser."""

    def test_import_phenotypes_command_succeeds(self, pheno_import_instance):
        # RST line 196: import_phenotypes .../ssc_pheno.yaml.
        assert_command_succeeds(
            pheno_import_instance.pheno_import,
            rst_ref=f"{RST}:196",
            expectation=(
                "import_phenotypes example_imports/pheno_import/"
                "ssc_pheno.yaml succeeds"
            ),
        )

    def test_ssc_pheno_visible_on_home_page(self, wgpf_server):
        # RST lines 204-205: on the Home Page you should see the ssc_pheno
        # phenotype study.
        resp = wgpf_server.client.get("/api/v3/datasets/visible")
        assert_dataset_visible(
            resp, "ssc_pheno",
            rst_ref=f"{RST}:204",
            expectation=(
                "on the GPF instance Home Page, you should see the "
                "`ssc_pheno` phenotype study"
            ),
        )

    def test_phenotype_browser_lists_imported_instrument(self, wgpf_server):
        # RST lines 205-206: following the link shows the Phenotype Browser
        # tab with the imported data; the instruments endpoint backs that
        # listing.
        resp = wgpf_server.client.get(
            "/api/v3/pheno_browser/instruments",
            params={"dataset_id": "ssc_pheno"},
        )
        assert_pheno_instruments_available(
            resp, [PHENO_INSTRUMENT],
            rst_ref=f"{RST}:206",
            expectation=(
                "following the link shows the Phenotype Browser tab with "
                "the imported data (the proband_measures instrument)"
            ),
        )

    def test_phenotype_browser_search_returns_measures(self, wgpf_server):
        # RST lines 205-206: the Phenotype Browser shows the imported data.
        # The measures endpoint reads the per-study browser DB that
        # `wgpf run` builds on startup — a non-empty result also confirms
        # that build happened (an un-built browser DB returns []).
        resp = wgpf_server.client.get(
            "/api/v3/pheno_browser/measures",
            params={
                "dataset_id": "ssc_pheno",
                "instrument": PHENO_INSTRUMENT,
            },
        )
        assert_pheno_measures_present(
            resp,
            rst_ref=f"{RST}:206",
            expectation=(
                "in the Phenotype Browser of ssc_pheno you can browse the "
                "imported measures (searching the proband_measures "
                "instrument returns measures)"
            ),
        )


class TestConfigureSscDenovoPheno:
    """RST lines 213-258: adding ``phenotype_data: ssc_pheno`` to the
    ssc_denovo study config enables the Phenotype Browser + Phenotype Tool
    tabs for that genotype study."""

    def _description(self, wgpf_server):
        return wgpf_server.client.get("/api/v3/datasets/ssc_denovo")

    def test_ssc_denovo_has_phenotype_data_attached(self, wgpf_server):
        # The `phenotype_data: ssc_pheno` line was added to the ssc_denovo
        # config by the pheno_import_instance fixture (RST line 243);
        # confirm the attachment took.
        assert_dataset_description_flag(
            self._description(wgpf_server), "phenotype_data",
            rst_ref=f"{RST}:243",
            expectation=(
                "adding `phenotype_data: ssc_pheno` to the ssc_denovo "
                "config attaches the phenotype study"
            ),
        )

    def test_ssc_denovo_phenotype_browser_enabled(self, wgpf_server):
        # RST lines 245-247: the Phenotype Browser tab is enabled for the
        # ssc_denovo study after configuring phenotype data.
        assert_dataset_description_flag(
            self._description(wgpf_server), "phenotype_browser",
            rst_ref=f"{RST}:246",
            expectation=(
                "the Phenotype Browser tab is enabled for the ssc_denovo "
                "study after configuring its phenotype data"
            ),
        )

    def test_ssc_denovo_phenotype_tool_enabled(self, wgpf_server):
        # RST lines 245-247: the Phenotype Tool tab is enabled for the
        # ssc_denovo study after configuring phenotype data.
        assert_dataset_description_flag(
            self._description(wgpf_server), "phenotype_tool",
            rst_ref=f"{RST}:246",
            expectation=(
                "the Phenotype Tool tab is enabled for the ssc_denovo "
                "study after configuring its phenotype data"
            ),
        )
