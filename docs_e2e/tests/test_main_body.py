"""Guide-claim tests for the main body of getting_started.rst.

Each test asserts one discrete claim that the guide makes. The
``rst_ref`` and ``expectation`` strings come straight from the
guide's prose — when a test fails, the message points at the
exact RST line that's wrong (or the regression that broke it).

Strict mode (#871 § Strict mode): tests run only what the guide
tells users to run. Imports + dataset config happen in the
session-scoped ``prepared_instance`` fixture in conftest.py;
this file just asserts the resulting state.
"""

from docs_e2e.guide_assertions import (
    assert_command_succeeds,
    assert_dataset_visible,
    assert_file_created,
)


class TestDenovoImport:
    """`getting_started.rst` lines ~149–246: importing the
    de novo example study via ``import_genotypes``."""

    def test_import_genotypes_command_succeeds(self, prepared_instance):
        assert_command_succeeds(
            prepared_instance.denovo_import,
            rst_ref="getting_started.rst:181",
            expectation=(
                "import_genotypes input_genotype_data/denovo_example.yaml "
                "succeeds"
            ),
        )

    def test_study_yaml_created(self, prepared_instance):
        path = (
            prepared_instance.instance_dir
            / "studies" / "denovo_example" / "denovo_example.yaml"
        )
        assert_file_created(
            path,
            rst_ref="getting_started.rst:199",
            expectation=(
                "minimal_instance/studies/denovo_example.yaml is created "
                "after the de novo import"
            ),
            after_command=prepared_instance.denovo_import,
        )

    def test_denovo_example_visible_on_home_page(self, wgpf_server):
        resp = wgpf_server.client.get("/api/v3/datasets/visible")
        assert_dataset_visible(
            resp, "denovo_example",
            rst_ref="getting_started.rst:213",
            expectation=(
                "The home page of the GPF system will show the imported "
                "study `denovo_example`"
            ),
        )


class TestVcfImport:
    """`getting_started.rst` lines ~250–305: importing the
    VCF example study via ``import_genotypes``."""

    def test_import_genotypes_command_succeeds(self, prepared_instance):
        assert_command_succeeds(
            prepared_instance.vcf_import,
            rst_ref="getting_started.rst:269",
            expectation=(
                "import_genotypes input_genotype_data/vcf_example.yaml "
                "succeeds"
            ),
        )

    def test_study_yaml_created(self, prepared_instance):
        path = (
            prepared_instance.instance_dir
            / "studies" / "vcf_example" / "vcf_example.yaml"
        )
        assert_file_created(
            path,
            rst_ref="getting_started.rst:280",
            expectation=(
                "minimal_instance/studies/vcf_example.yaml is created "
                "after the VCF import"
            ),
            after_command=prepared_instance.vcf_import,
        )

    def test_vcf_example_visible_on_home_page(self, wgpf_server):
        resp = wgpf_server.client.get("/api/v3/datasets/visible")
        assert_dataset_visible(
            resp, "vcf_example",
            rst_ref="getting_started.rst:280",
            expectation=(
                "The GPF instance Home Page now includes the imported "
                "study `vcf_example`"
            ),
        )


class TestExampleDataset:
    """`getting_started.rst` lines ~307–348: combining the two
    studies into ``example_dataset``."""

    def test_example_dataset_yaml_present(self, prepared_instance):
        assert_file_created(
            prepared_instance.dataset_yaml_path,
            rst_ref="getting_started.rst:322",
            expectation=(
                "datasets/example_dataset/example_dataset.yaml is created "
                "with the studies block listing denovo_example + vcf_example"
            ),
        )

    def test_example_dataset_visible_on_home_page(self, wgpf_server):
        resp = wgpf_server.client.get("/api/v3/datasets/visible")
        assert_dataset_visible(
            resp, "example_dataset",
            rst_ref="getting_started.rst:335",
            expectation=(
                "the home page of the GPF instance will change and now "
                "will include the configured dataset `example_dataset`"
            ),
        )

    def test_denovo_example_still_visible(self, wgpf_server):
        # The example dataset GROUPS the two studies; it does not
        # remove them from the listing. Guard against a regression
        # that would silently hide the underlying studies.
        resp = wgpf_server.client.get("/api/v3/datasets/visible")
        assert_dataset_visible(
            resp, "denovo_example",
            rst_ref="getting_started.rst:335",
            expectation=(
                "after creating example_dataset, denovo_example is still "
                "listed alongside it"
            ),
        )

    def test_vcf_example_still_visible(self, wgpf_server):
        resp = wgpf_server.client.get("/api/v3/datasets/visible")
        assert_dataset_visible(
            resp, "vcf_example",
            rst_ref="getting_started.rst:335",
            expectation=(
                "after creating example_dataset, vcf_example is still "
                "listed alongside it"
            ),
        )
