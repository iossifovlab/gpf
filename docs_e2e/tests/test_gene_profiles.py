"""Guide-claim tests for getting_started_with_gene_profiles.rst.

The gene-profiles sub-guide configures and prebuilds the Gene Profile tool
on the same ``minimal_instance`` the earlier guides built:

1. **configure** — create ``minimal_instance/gene_profiles.yaml`` (which
   statistics, gene scores, gene sets, and gene links to collect per gene)
   and add a ``gene_profiles_config`` block to gpf_instance.yaml.
2. **prebuild** — run ``generate_gene_profile`` to populate the gene
   profiles DB (``gpdb.duckdb``). The guide's note offers a ``--genes`` form
   to limit generation to a short gene list instead of all 19,285 MANE
   genes; the suite runs that documented fast form.
3. **serve** — ``wgpf run`` then shows the Gene Profiles tool on the home
   page, an ``All Genes`` table of gene profiles, and a per-gene profile
   page (the guide's screenshot is CHD8).

The configure + prebuild steps live in the session-scoped
``gene_profiles_instance`` fixture (conftest.py); ``wgpf_server`` depends on
it, so the single shared server serves the profile-enabled instance.

Strict mode (#871): the fixture only does what the guide tells the user to
do — the file create, the one-block yaml edit, and the ``generate_gene_profile``
prebuild. The ``--genes`` form is the guide's own documented fast path (RST
lines 116-128), so the command runs verbatim with the guide's short gene list.

Each test maps to one discrete prose claim. ``rst_ref`` points at the line
in the guide source so a failure localizes the drift.
"""

from docs_e2e.guide_assertions import (
    assert_command_succeeds,
    assert_file_created,
    assert_gene_profile_for_gene,
    assert_gene_profile_table_rows,
    assert_gene_profiles_configured,
)

RST = "getting_started_with_gene_profiles.rst"

# The default dataset the gene_profiles.yaml configures (RST line 22 / the
# config's `default_dataset`).
_DEFAULT_DATASET = "ssc_denovo"

# The gene the guide's single-profile screenshot shows (RST line 156); it
# heads the --genes list the prebuild fixture runs.
_PROFILE_GENE = "CHD8"

# The ten genes the guide's note prebuilds (RST lines 125-127). PAGE_SIZE is
# 50, so all ten land on the first table/rows page.
_GENERATED_GENE_COUNT = 10

# Cold demand-pull budget: building the GPFInstance for the profile endpoints
# resolves the configured gene scores / gene set collections from the GRR on
# first access. Well above the shared client's default 60s, under the build
# wall.
_COLD_PULL_TIMEOUT = 300


class TestGenerateGeneProfile:
    """RST lines 101-128: prebuild the gene profiles with
    ``generate_gene_profile``."""

    def test_generate_gene_profile_succeeds(self, gene_profiles_instance):
        # RST lines 111-113 (+ the note's --genes form, 125-127): the
        # generate_gene_profile command prebuilds the gene profiles.
        assert_command_succeeds(
            gene_profiles_instance.generate,
            rst_ref=f"{RST}:112",
            expectation=(
                "generate_gene_profile prebuilds the gene profiles for the "
                "configured genes"
            ),
        )

    def test_generate_gene_profile_creates_gpdb(self, gene_profiles_instance):
        # The prebuild writes the gene profiles DB (gpdb.duckdb) into the
        # instance dir; wgpf loads it on startup to serve the tool. Backs the
        # "prebuild the gene profiles" claim (RST lines 101-113) at the
        # filesystem level, between command-success and server-serves.
        assert_file_created(
            gene_profiles_instance.gpdb_path,
            rst_ref=f"{RST}:112",
            expectation=(
                "generating gene profiles produces the gene profiles DB the "
                "instance serves"
            ),
            after_command=gene_profiles_instance.generate,
        )


class TestGeneProfilesTool:
    """RST lines 130-156: ``wgpf run`` serves the Gene Profiles tool."""

    def test_gene_profiles_tool_enabled(self, wgpf_server):
        # RST lines 137-142: on the home page you can see the Gene Profiles
        # tool. The single-view/configuration endpoint returns a non-empty
        # config exactly when the tool is enabled (the SPA gates its home-page
        # link on that); an empty {} would still be HTTP 200.
        resp = wgpf_server.client.get(
            "/api/v3/gene_profiles/single-view/configuration",
            timeout=_COLD_PULL_TIMEOUT,
        )
        assert_gene_profiles_configured(
            resp, default_dataset=_DEFAULT_DATASET,
            rst_ref=f"{RST}:136",
            expectation=(
                "the home page shows the Gene Profiles tool after configuring "
                "and prebuilding it"
            ),
        )

    def test_all_genes_table_has_rows(self, wgpf_server):
        # RST lines 144-149: following the `All Genes` link opens the Gene
        # Profiles table with information about genes. table/rows backs that
        # listing; the prebuilt ten genes all fit on page 1 (PAGE_SIZE 50),
        # and CHD8 must be among them.
        resp = wgpf_server.client.get(
            "/api/v3/gene_profiles/table/rows",
            timeout=_COLD_PULL_TIMEOUT,
        )
        assert_gene_profile_table_rows(
            resp,
            min_count=_GENERATED_GENE_COUNT,
            require_symbols=[_PROFILE_GENE],
            rst_ref=f"{RST}:143",
            expectation=(
                "the `All Genes` link opens the Gene Profiles table with "
                "information about the prebuilt genes"
            ),
        )

    def test_gene_profile_page_for_chd8(self, wgpf_server):
        # RST lines 151-156: selecting a gene from the table opens the Gene
        # Profile page for that gene (the screenshot is CHD8). The
        # single-view/gene/<symbol> endpoint backs that page.
        resp = wgpf_server.client.get(
            f"/api/v3/gene_profiles/single-view/gene/{_PROFILE_GENE}",
            timeout=_COLD_PULL_TIMEOUT,
        )
        assert_gene_profile_for_gene(
            resp, _PROFILE_GENE,
            rst_ref=f"{RST}:155",
            expectation=(
                "selecting a gene opens its Gene Profile page (CHD8 in the "
                "guide screenshot)"
            ),
        )
