# pylint: disable=W0621,C0114,C0116,W0212,W0613

def test_trios2_study_simple(trios2_study):
    config = trios2_study.config

    assert config is not None
    assert config.denovo_gene_sets is not None

    assert config.denovo_gene_sets.enabled


def test_default_dgs_config_selected_person_sets(trios2_study):
    config = trios2_study.config

    assert config.denovo_gene_sets.selected_person_set_collections == \
        ["status"]


def test_default_dgs_config_standard_criterias_effect_types(trios2_study):
    config = trios2_study.config

    assert "effect_types" in config.denovo_gene_sets.standard_criterias

    effect_types = config.denovo_gene_sets.standard_criterias.effect_types
    assert effect_types == {
        "segments": {
            "LGDs": "LGDs",
            "Missense": "missense",
            "Synonymous": "synonymous",
        },
    }


def test_default_dgs_config_standard_criterias_sexes(trios2_study):
    config = trios2_study.config

    assert "sexes" in config.denovo_gene_sets.standard_criterias

    sexes = config.denovo_gene_sets.standard_criterias.sexes
    assert sexes == {
        "segments": {
            "Female": "F",
            "Male": "M",
            "Unspecified": "U",
        },
    }


def test_default_dgs_config_recurrency_criteria(trios2_study):
    config = trios2_study.config

    assert "segments" in config.denovo_gene_sets.recurrency_criteria

    segments = config.denovo_gene_sets.recurrency_criteria.segments
    assert segments["Single"] == {
        "start": 1,
        "end": 2,
    }

    assert segments["Triple"] == {
        "start": 3,
        "end": -1,
    }

    assert segments["Recurrent"] == {
        "start": 2,
        "end": -1,
    }
