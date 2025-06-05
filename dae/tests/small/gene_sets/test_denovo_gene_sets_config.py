# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap
from typing import Any, cast

import pytest
import yaml

from dae.gene_sets.denovo_gene_sets_config import (
    EffectsCriteria,
    RecurrentCriteria,
    SexesCriteria,
    SingleCriteria,
    TripleCriteria,
    create_denovo_gene_set_spec,
    parse_denovo_gene_sets_config,
)
from dae.studies.study import GenotypeData
from dae.variants.attributes import Sex


def test_trios2_study_simple(
    trios2_study: GenotypeData,
) -> None:
    config = trios2_study.config

    assert config is not None
    assert config.denovo_gene_sets is not None

    assert config.denovo_gene_sets.enabled


def test_default_dgs_config_standard_criterias_effect_types(
    trios2_study: GenotypeData,
) -> None:
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


def test_default_dgs_config_standard_criterias_sexes(
    trios2_study: GenotypeData,
) -> None:
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


def test_default_dgs_config_recurrency_criteria(
    trios2_study: GenotypeData,
) -> None:
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


def test_explore_new_style_configs() -> None:
    effects = EffectsCriteria(
        name="LGDs",
        effects=["LGDs"],
    )
    assert effects.name == "LGDs"
    assert effects.effects == [
        "nonsense",
        "splice-site",
        "no-frame-shift-newStop",
        "frame-shift",
    ]

    sexes = SexesCriteria(
        name="Female",
        sexes=[Sex.F],
    )
    assert sexes.name == "Female"
    assert sexes.sexes == [Sex.F]

    single = SingleCriteria(
        name="Single",
        start=1,
        end=2,
    )
    assert single.name == "Single"
    assert single.start == 1
    assert single.end == 2

    recurrent = RecurrentCriteria(
        name="Recurrent",
        start=2,
        end=-1,
    )
    assert recurrent.name == "Recurrent"
    assert recurrent.start == 2
    assert recurrent.end == -1

    triple = TripleCriteria(
        name="Triple",
        start=3,
        end=-1,
    )
    assert triple.name == "Triple"
    assert triple.start == 3
    assert triple.end == -1

    with pytest.raises(ValueError, match="Invalid effect type: Missense"):
        EffectsCriteria(
            name="LGDs",
            effects=["LGDs", "Missense"],
        )


@pytest.fixture
def denovo_gene_sets_config() -> dict[str, Any]:
    content = textwrap.dedent("""
  enabled: true
  selected_person_set_collections:
  - phenotype
  standard_criterias:
    effect_types:
      segments:
        LGDs: LGDs
        Missense: missense
        Synonymous: synonymous
    sexes:
      segments:
        Female: F
        Male: M
        Unspecified: U
  recurrency_criteria:
    segments:
      Single:
          start: 1
          end: 2
      Triple:
          start: 3
          end: -1
      Recurrent:
          start: 2
          end: -1
  gene_sets_names:
  - LGDs
  - LGDs.Male
  - LGDs.Female
  - LGDs.Recurrent
  - LGDs.Single
  - LGDs.Triple
  - Missense
  - Missense.Male
  - Missense.Female
  - Missense.Recurrent
  - Missense.Triple
  - Synonymous
  - Synonymous.Male
  - Synonymous.Female
  - Synonymous.Recurrent
  - Synonymous.Triple
    """)
    return cast(dict[str, Any], yaml.safe_load(content))


def test_parse_denovo_gene_sets_config(
    denovo_gene_sets_config: dict[str, Any],
) -> None:
    config = parse_denovo_gene_sets_config(
        denovo_gene_sets_config)
    assert config is not None


@pytest.mark.parametrize("gene_set_id,count", [
    ("LGDs.Triple", 2),
    ("LGDs.Male.Single", 3),
    ("Synonymous", 1),
    ("Synonymous.Recurrent", 2),
])
def test_create_denovo_sene_set_spec(
    denovo_gene_sets_config: dict[str, Any],
    gene_set_id: str,
    count: int,
) -> None:
    config = parse_denovo_gene_sets_config(
        denovo_gene_sets_config)
    assert config is not None

    gene_set_spec = create_denovo_gene_set_spec(
        gene_set_id,
        config,
    )
    assert gene_set_spec is not None
    assert len(gene_set_spec.criterias) == count
    assert gene_set_spec.gene_set_id == gene_set_id
