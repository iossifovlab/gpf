# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pytest
from box import Box

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.study_config import study_config_schema


@pytest.fixture(scope="module")
def quads_f1_config(tmp_path_factory: pytest.TempPathFactory) -> Box:
    config_contents =  textwrap.dedent("""
        name = "QUADS_F1"
        id = "quads_f1"
        phenotype_data = "quads_f1"

        phenotype_tool = true
        phenotype_browser = false

        [genotype_storage]
        id = "genotype_filesystem"
        files.pedigree = {path = "data/quads_f1.ped", params = { ped_family= "familyId", ped_person= "personId", ped_mom= "momId"}}  # noqa

        [[genotype_storage.files.variants]]
        path = "data/quads_f1.vcf"
        format = "vcf"
        params = {vcf_denovo_mode = "denovo"}

        [genotype_browser]
        enabled = true
        has_present_in_child = false
        has_present_in_parent = false
        has_family_filters = false
        has_pedigree_selector = true

        [genotype_browser.family_filters]
        categorical.name = "Categorical"
        categorical.from = "phenodb"
        categorical.source = "instrument1.categorical"
        categorical.source_type = "categorical"
        categorical.filter_type = "single"
        categorical.role = "prb"

        continuous.name = "Continuous"
        continuous.from = "phenodb"
        continuous.source = "instrument1.continuous"
        continuous.source_type = "continuous"
        continuous.filter_type = "single"
        continuous.role = "prb"

        [genotype_browser.columns.genotype]
        ssc_freq.name = "SSC"
        ssc_freq.source = "SSC-freq"
        ssc_freq.format = "SSC %%.2f %%%%"

        evs_freq.name = "EVS"
        evs_freq.source = "EVS-freq"
        evs_freq.format = "EVS %%.2f %%%%"

        e65_freq.name = "E65"
        e65_freq.source = "E65-freq"
        e65_freq.format = "E65 %%.2f %%%%"

        [genotype_browser.columns.phenotype]
        prb_con.name = "Continuous Proband"
        prb_con.source = "instrument1.continuous"
        prb_con.role = "prb"

        prb_cat.name = "Categorical"
        prb_cat.source = "instrument1.categorical"
        prb_cat.role = "prb"

        prb_ord.name = "Ordinal"
        prb_ord.source = "instrument1.ordinal"
        prb_ord.role = "prb"

        prb_raw.name = "Raw"
        prb_raw.source = "instrument1.raw"
        prb_raw.role = "prb"
    """)
    root_dir = tmp_path_factory.mktemp("quads_f1_test_config")
    config_file = root_dir / "quads_f1.conf"
    config_file.write_text(config_contents)

    (root_dir / "data").mkdir()
    (root_dir / "data" / "quads_f1.ped").touch()
    (root_dir / "data" / "quads_f1.vcf").touch()

    return GPFConfigParser.load_config(str(config_file), study_config_schema)


def test_study_config_simple(genotype_data_study_configs):
    assert genotype_data_study_configs is not None
    assert list(genotype_data_study_configs.keys())


def test_study_config_year(genotype_data_study_configs):
    study_config = genotype_data_study_configs.get("inheritance_trio")
    assert study_config is not None
    assert study_config.year is None


def test_quads_f1_config_genotype_storage(quads_f1_config):
    assert quads_f1_config is not None

    assert quads_f1_config.genotype_storage.id == "genotype_filesystem"


@pytest.mark.parametrize(
    "option_name,expected_value",
    [
        ("name", "QUADS_F1"),
        ("id", "quads_f1"),
        ("phenotype_tool", True),
        ("phenotype_browser", False),
        ("phenotype_data", "quads_f1"),
        ("year", None),
        ("pub_med", None),
    ],
)
def test_quads_f1_config_attr_access(
    quads_f1_config, option_name, expected_value
):
    assert quads_f1_config is not None
    assert getattr(quads_f1_config, option_name) == expected_value


@pytest.mark.parametrize(
    "option_name,expected_value",
    [
        ("has_present_in_child", False),
        ("has_present_in_parent", False),
        ("has_family_filters", False),
        ("has_pedigree_selector", True),
    ],
)
def test_quads_f1_config_genotype_browser(
    quads_f1_config, option_name, expected_value
):
    genotype_browser_config = quads_f1_config.genotype_browser

    assert getattr(genotype_browser_config, option_name) == expected_value


def test_quads_f1_config_genotype_browser_pheno_filters(quads_f1_config):
    genotype_browser_config = quads_f1_config.genotype_browser

    assert genotype_browser_config.family_filters == {
        "categorical": {
            "name": "Categorical",
            "from": "phenodb",
            "source": "instrument1.categorical",
            "source_type": "categorical",
            "filter_type": "single",
            "role": "prb",
        },
        "continuous": {
            "name": "Continuous",
            "from": "phenodb",
            "source": "instrument1.continuous",
            "source_type": "continuous",
            "filter_type": "single",
            "role": "prb",
        }
    }


def test_quads_f1_config_genotype_browser_columns(quads_f1_config):
    assert len(quads_f1_config.genotype_browser.columns.genotype) == 3


def test_quads_f1_config_genotype_browser_pheno_columns(quads_f1_config):
    assert len(quads_f1_config.genotype_browser.columns.phenotype) == 4


def test_quads_f1_files_and_tables(quads_f1_config):
    assert quads_f1_config.genotype_storage.files.variants[0].path.endswith(
        "data/quads_f1.vcf"
    )
    assert quads_f1_config.genotype_storage.files.pedigree.path.endswith(
        "data/quads_f1.ped"
    )


def test_quads_f1_config_files(quads_f1_config):
    assert quads_f1_config.genotype_storage.files is not None
    assert quads_f1_config.genotype_storage.files.pedigree is not None
    assert quads_f1_config.genotype_storage.files.pedigree.path.endswith(
        "/data/quads_f1.ped"
    )
    assert len(quads_f1_config.genotype_storage.files.pedigree.params) == 3
