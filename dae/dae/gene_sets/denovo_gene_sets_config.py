from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
)
from pydantic.functional_validators import AfterValidator

from dae.effect_annotation.annotation_effects import get_effect_types
from dae.variants.attributes import Sex


def _validate_effect_types(effect_types: list[str]) -> list[str]:
    available_effect_types = set(get_effect_types(types=True, groups=True))
    for effect_type in effect_types:
        if effect_type not in available_effect_types:
            raise ValueError(f"Invalid effect type: {effect_type}")
    return effect_types


EffectTypes = Annotated[
    list[str],
    AfterValidator(_validate_effect_types),
]


class EffectsCriteria(BaseModel):
    """Criteria for filtering effect types."""
    model_config = ConfigDict(extra="forbid")

    name: str
    effects: EffectTypes


class SexesCriteria(BaseModel):
    """Criteria for filtering sexes."""

    model_config = ConfigDict(extra="forbid")

    name: str
    sexes: list[Sex]


class RecurrencyCriteria(BaseModel):
    """Criteria for filtering recurrency."""

    model_config = ConfigDict(extra="forbid")

    name: str
    start: int  # closed interval
    end: int  # open interval


class SingleCriteria(RecurrencyCriteria):
    """Single recurrency criteria."""

    name: Literal["Single"]
    start: Literal[1]
    end: Literal[2]


class RecurrentCriteria(RecurrencyCriteria):
    """Recurrent recurrency criteria."""
    name: Literal["Recurrent"]
    start: Literal[2]
    end: Literal[-1]


class TripleCriteria(RecurrencyCriteria):
    """Triple recurrency criteria."""
    name: Literal["Triple"]
    start: Literal[3]
    end: Literal[-1]


class DenovoGeneSetsConfig(BaseModel):
    """Configuration for de novo gene sets."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    selected_person_set_collections: list[str]

    effect_types: dict[str, EffectsCriteria]
    sexes: dict[str, SexesCriteria]
    recurrency: dict[str, RecurrencyCriteria]

    gene_sets_names: list[str]


def _validate_gene_sets_names(
    gene_sets_names: list[str],
    effect_types: dict[str, EffectsCriteria],
    sexes: dict[str, SexesCriteria],
    recurrency: dict[str, RecurrencyCriteria],
) -> list[str]:
    for gene_set_name in gene_sets_names:
        segements = gene_set_name.split(".")
        for segment in segements:
            if segment in effect_types:
                continue
            if segment in sexes:
                continue
            if segment in recurrency:
                continue
            raise ValueError(
                f"Invalid gene set name: {gene_set_name}; "
                f"bad segement: {segment}")

    return gene_sets_names


def parse_denovo_gene_sets_config(
    config: dict[str, Any],
) -> DenovoGeneSetsConfig:
    """Parse de novo gene sets configuration."""
    enabled = config.get("enabled", False)
    selected_person_set_collections = config.get(
        "selected_person_set_collections", [])
    if not selected_person_set_collections:
        raise ValueError("No person set collections selected")
    selected_starndard_criterias_values = config.get(
        "selected_starndard_criterias_values", ["effect_types", "sexes"])
    if not selected_starndard_criterias_values:
        raise ValueError("No standard criterias values selected")
    for cn in selected_starndard_criterias_values:
        if cn not in ["effect_types", "sexes"]:
            raise ValueError(f"Invalid standard criteria: {cn}")
    standard_criterias = config.get("standard_criterias", {})
    if not standard_criterias:
        raise ValueError("No standard criterias defined")
    for criteria_name in selected_starndard_criterias_values:
        if criteria_name not in standard_criterias:
            raise ValueError(
                f"Standard criteria {criteria_name} not defined")
    effect_types = {}
    if "effect_types" in selected_starndard_criterias_values:
        criteria_segments = standard_criterias["effect_types"]["segments"]
        effect_types = {
            name: EffectsCriteria(name=name, effects=[effect])
            for name, effect in criteria_segments.items()
        }
    sexes = {}
    if "sexes" in selected_starndard_criterias_values:
        criteria_segments = standard_criterias["sexes"]["segments"]
        sexes = {
            name: SexesCriteria(name=name, sexes=[Sex.from_name(sex)])
            for name, sex in criteria_segments.items()
        }
    recurrency = {}
    recurrency_criteria = config.get("recurrency_criteria", {})
    if recurrency_criteria:
        criteria_segments = recurrency_criteria["segments"]
        recurrency = {
            name: RecurrencyCriteria(name=name, **criteria)
            for name, criteria in criteria_segments.items()
        }

    gene_sets_names = _validate_gene_sets_names(
        config.get("gene_sets_names", []),
        effect_types=effect_types,
        sexes=sexes,
        recurrency=recurrency,
    )
    if not gene_sets_names:
        raise ValueError("No gene sets names defined")

    return DenovoGeneSetsConfig(
        enabled=enabled,
        selected_person_set_collections=selected_person_set_collections,
        effect_types=effect_types,
        sexes=sexes,
        recurrency=recurrency,
        gene_sets_names=gene_sets_names,
    )


class DenovoGeneSetSpec(BaseModel):
    """De novo gene set specification."""

    model_config = ConfigDict(extra="forbid")

    name: str
    criterias: dict[
        str,
        EffectsCriteria | SexesCriteria | RecurrencyCriteria,
    ]

    def _str_(self) -> str:
        return self.name


def create_denovo_gene_set_spec(
    gene_set_name: str,
    config: DenovoGeneSetsConfig,
) -> DenovoGeneSetSpec:
    """Create de novo gene set specification from name."""
    segments = gene_set_name.split(".")
    criterias: dict[
        str, EffectsCriteria | SexesCriteria | RecurrencyCriteria] = {}

    for segment in segments:
        if segment in config.effect_types:
            criterias[segment] = config.effect_types[segment]
            continue
        if segment in config.sexes:
            criterias[segment] = config.sexes[segment]
            continue
        if segment in config.recurrency:
            criterias[segment] = config.recurrency[segment]
            continue
        raise ValueError(f"Invalid segment: {segment}")
    return DenovoGeneSetSpec(
        name=gene_set_name,
        criterias=criterias,
    )


def generate_denovo_gene_sets_specs(
    config: DenovoGeneSetsConfig,
) -> dict[str, Any]:
    """Generate de novo gene sets specs."""
    return {
        gene_set_name: create_denovo_gene_set_spec(gene_set_name, config)
        for gene_set_name in config.gene_sets_names
    }
