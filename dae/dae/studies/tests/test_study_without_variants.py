"""Tests genotype study without genotype data."""
# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pytest
import toml


from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.study_config import study_config_schema
from dae.studies.study import GenotypeDataStudy
from dae.common_reports.common_report import CommonReport


@pytest.fixture
def no_variants_study(gpf_instance_2013, tmp_path):
    """Build a study without genotype data fixture."""
    content = textwrap.dedent(
        """
        id = "test_study"
        name = "Test Phenotypes"

        conf_dir = "."
        has_denovo = false
        has_cnv = false

        enabled = true

        [genotype_browser]
        enabled = false

        [genotype_storage.tables]
        pedigree = "test_study_pedigree"


        [denovo_gene_sets]
        enabled = false

        [gene_browser]
        enabled = false
        """)
    assert content is not None

    default_config = GPFConfigParser.parse_and_interpolate_file(
        gpf_instance_2013.dae_config.default_study_config.conf_file)
    parsed_content = GPFConfigParser.parse_and_interpolate(
        content, parser=toml.loads)
    tmp_path.mkdir(exist_ok=True)
    config = GPFConfigParser.process_config(
        parsed_content, study_config_schema, default_config, tmp_path)

    genotype_storage = \
        gpf_instance_2013.genotype_storages.get_genotype_storage(
            "genotype_impala"
        )

    backend = genotype_storage.build_backend(
        config, gpf_instance_2013.reference_genome,
        gpf_instance_2013.gene_models)

    return GenotypeDataStudy(config, backend)


def test_study_simple(no_variants_study):
    """Test variants query for study without variants."""
    assert no_variants_study
    assert no_variants_study.study_id == "test_study"

    fvs = list(no_variants_study.query_variants())
    assert len(fvs) == 0


def test_common_reports(no_variants_study):
    """Test building a common report from a study without variants."""
    common_report = CommonReport.build_report(no_variants_study)
    assert common_report
