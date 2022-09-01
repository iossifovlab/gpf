# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pytest


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
    assert len(quads_f1_config.genotype_browser.columns.genotype) == 23


def test_quads_f1_config_genotype_browser_pheno_columns(quads_f1_config):
    assert len(quads_f1_config.genotype_browser.columns.phenotype) == 4


def test_quads_f1_files_and_tables(quads_f1_config):
    assert quads_f1_config.genotype_storage.files.variants[0].path.endswith(
        "data/quads_f1.vcf"
    )
    assert quads_f1_config.genotype_storage.files.pedigree.path.endswith(
        "data/quads_f1.ped"
    )
    # assert quads_f1_config.files.denovo[0].path.endswith(
    #     'data/quads_f1_denovo.tsv')

    # assert quads_f1_config.tables.variant == 'quads_f1_variant'
    # assert quads_f1_config.tables.pedigree == 'quads_f1_pedigree'


def test_quads_f1_config_work_dir(quads_f1_config, studies_dir):
    assert quads_f1_config.work_dir == os.path.join(studies_dir, "quads_f1")


def test_quads_f1_config_files(quads_f1_config):
    assert quads_f1_config.genotype_storage.files is not None
    assert quads_f1_config.genotype_storage.files.pedigree is not None
    assert quads_f1_config.genotype_storage.files.pedigree.path.endswith(
        "/data/quads_f1.ped"
    )
    assert len(quads_f1_config.genotype_storage.files.pedigree.params) == 3
