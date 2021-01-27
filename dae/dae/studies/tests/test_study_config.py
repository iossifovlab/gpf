import os
import pytest
from dae.studies.tests.conftest import studies_dir


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
        ("description", "QUADS F1"),
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
        ("has_study_filters", True),
    ],
)
def test_quads_f1_config_genotype_browser(
    quads_f1_config, option_name, expected_value
):
    genotype_browser_config = quads_f1_config.genotype_browser

    assert getattr(genotype_browser_config, option_name) == expected_value


def test_quads_f1_config_genotype_browser_pheno_filters(quads_f1_config):
    genotype_browser_config = quads_f1_config.genotype_browser

    assert genotype_browser_config.pheno_filters == {
        "categorical": {
            "name": "Categorical",
            "measure_type": "categorical",
            "filter_type": "single",
            "role": "prb",
            "measure": "instrument1.categorical",
        },
        "continuous": {
            "name": "Continuous",
            "measure_type": "continuous",
            "filter_type": "single",
            "role": "prb",
            "measure": "instrument1.continuous",
        }
    }


# def test_quads_f1_config_genotype_browser_present_in_role(quads_f1_config):
#     genotype_browser_config = quads_f1_config.genotype_browser

#     assert set(genotype_browser_config.present_in_role.keys()) == {
#         "prb", "parent"
#     }
#     assert (
#         genotype_browser_config.present_in_role.prb.name
#         == "Present in Proband and Sibling"
#     )
#     assert set(genotype_browser_config.present_in_role.prb.roles) == {
#         "prb", "sib"
#     }

#     assert genotype_browser_config.present_in_role.parent.name == "Parents"
#     assert set(genotype_browser_config.present_in_role.parent.roles) == {
#         "mom", "dad"
#     }


@pytest.mark.parametrize(
    "option_name,expected_name,expected_source,expected_slots",
    [
        (
            "genotype",
            "genotype",
            "pedigree",
            [
                {
                    "source": "inChS",
                    "name": "in child",
                    "id": "genotype.in child",
                    "format": "%s",
                },
                {
                    "source": "fromParentS",
                    "name": "from parent",
                    "id": "genotype.from parent",
                    "format": "%s",
                },
            ],
        ),
        (
            "effect",
            "effect",
            None,
            [
                {
                    "source": "worstEffect",
                    "name": "worst effect type",
                    "id": "effect.worst effect type",
                    "format": "%s",
                },
                {
                    "source": "genes",
                    "name": "genes",
                    "id": "effect.genes",
                    "format": "%s",
                },
            ],
        ),
        ("best", "family genotype", "bestSt", []),
    ],
)
def test_quads_f1_config_genotype_browser_columns(
    quads_f1_config,
    option_name,
    expected_name,
    expected_source,
    expected_slots,
):
    genotype_browser_config = quads_f1_config.genotype_browser

    assert len(genotype_browser_config.genotype) == 19

    genotype_column = genotype_browser_config.genotype[option_name]

    assert genotype_column.name == expected_name
    assert genotype_column.source == expected_source

    if genotype_column.slots:
        assert len(genotype_column.slots) == len(expected_slots)

        for gc_slot, e_slot in zip(genotype_column.slots, expected_slots):
            assert gc_slot.source == e_slot["source"]
            assert gc_slot.name == e_slot["name"]
            assert gc_slot.format == e_slot["format"]


@pytest.mark.parametrize(
    "option_name,expected_name,expected_source,expected_slots",
    [
        (
            "continuous",
            "Continuous",
            None,
            [
                {
                    "id": "continuous.Continuous",
                    "name": "Continuous",
                    "role": "prb",
                    "source": "instrument1.continuous",
                    "format": "%s",
                }
            ],
        ),
        (
            "categorical",
            "Categorical",
            None,
            [
                {
                    "id": "categorical.Categorical",
                    "name": "Categorical",
                    "role": "prb",
                    "source": "instrument1.categorical",
                    "format": "%s",
                }
            ],
        ),
        (
            "ordinal",
            "Ordinal",
            None,
            [
                {
                    "id": "ordinal.Ordinal",
                    "name": "Ordinal",
                    "role": "prb",
                    "source": "instrument1.ordinal",
                    "format": "%s",
                }
            ],
        ),
        (
            "raw",
            "Raw",
            None,
            [
                {
                    "id": "raw.Raw",
                    "name": "Raw",
                    "role": "prb",
                    "source": "instrument1.raw",
                    "format": "%s",
                }
            ],
        ),
    ],
)
def test_quads_f1_config_genotype_browser_pheno_columns(
    quads_f1_config,
    option_name,
    expected_name,
    expected_source,
    expected_slots,
):
    genotype_browser_config = quads_f1_config.genotype_browser

    assert len(genotype_browser_config.genotype) == 19

    genotype_column = genotype_browser_config.pheno[option_name]
    assert genotype_column.name == expected_name
    assert genotype_column.source == expected_source

    if genotype_column.slots:
        assert len(genotype_column.slots) == len(expected_slots)

        for gc_slot, e_slot in zip(genotype_column.slots, expected_slots):
            assert gc_slot.source == e_slot["source"]
            assert gc_slot.name == e_slot["name"]
            assert gc_slot.format == e_slot["format"]


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


def test_quads_f1_config_work_dir(quads_f1_config):
    assert quads_f1_config.work_dir == os.path.join(studies_dir(), "quads_f1")


def test_quads_f1_config_files(quads_f1_config):
    assert quads_f1_config.genotype_storage.files is not None
    assert quads_f1_config.genotype_storage.files.pedigree is not None
    assert quads_f1_config.genotype_storage.files.pedigree.path.endswith(
        "/data/quads_f1.ped"
    )
    assert len(quads_f1_config.genotype_storage.files.pedigree.params) == 3
