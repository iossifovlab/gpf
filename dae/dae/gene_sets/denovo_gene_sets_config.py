from __future__ import annotations

from collections.abc import Iterable
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
)
from pydantic.functional_validators import AfterValidator

from dae.effect_annotation.annotation_effects import (
    get_effect_types,
    get_effect_types_set,
)
from dae.variants.attributes import Sex


def _validate_effect_types(effect_types: Iterable[str]) -> list[str]:
    available_effect_types = set(get_effect_types(types=True, groups=True))
    for effect_type in effect_types:
        if effect_type not in available_effect_types:
            raise ValueError(f"Invalid effect type: {effect_type}")
    return list(get_effect_types_set(effect_types))


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


class RecurrencyCriteriaBase(BaseModel):
    """Criteria for filtering recurrency."""

    model_config = ConfigDict(extra="forbid")

    name: str
    start: int  # closed interval
    end: int  # open interval


class SingleCriteria(RecurrencyCriteriaBase):
    """Single recurrency criteria."""

    name: Literal["Single"]
    start: Literal[1]
    end: Literal[2]


class RecurrentCriteria(RecurrencyCriteriaBase):
    """Recurrent recurrency criteria."""
    name: Literal["Recurrent"]
    start: Literal[2]
    end: Literal[-1]


class TripleCriteria(RecurrencyCriteriaBase):
    """Triple recurrency criteria."""
    name: Literal["Triple"]
    start: Literal[3]
    end: Literal[-1]


RecurrencyCriteria = SingleCriteria | RecurrentCriteria | TripleCriteria


def parse_recurrency_criteria(
    name: str,
    recurrency_criteria: dict[str, Any],
) -> RecurrencyCriteria:
    """Parse recurrency criteria."""
    if name == "Single":
        return SingleCriteria(
            name="Single",
            start=recurrency_criteria["start"],
            end=recurrency_criteria["end"],
        )
    if name == "Recurrent":
        return RecurrentCriteria(
            name="Recurrent",
            start=recurrency_criteria["start"],
            end=recurrency_criteria["end"],
        )
    if name == "Triple":
        return TripleCriteria(
            name="Triple",
            start=recurrency_criteria["start"],
            end=recurrency_criteria["end"],
        )
    raise ValueError(f"Invalid recurrency criteria: {name}")


class DenovoGeneSetsConfig(BaseModel):
    """Configuration for de novo gene sets."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    selected_person_set_collections: list[str]

    effect_types: dict[str, EffectsCriteria]
    sexes: dict[str, SexesCriteria]
    recurrency: dict[str, RecurrencyCriteria]

    gene_sets_ids: list[str]


def _validate_gene_sets_ids(
    gene_sets_ids: list[str],
    effect_types: dict[str, EffectsCriteria],
    sexes: dict[str, SexesCriteria],
    recurrency: dict[str, RecurrencyCriteria],
) -> list[str]:
    for gene_set_id in gene_sets_ids:
        segements = gene_set_id.split(".")
        for segment in segements:
            if segment in effect_types:
                continue
            if segment in sexes:
                continue
            if segment in recurrency:
                continue
            raise ValueError(
                f"Invalid gene set name: {gene_set_id}; "
                f"bad segement: {segment}")

    return gene_sets_ids


def parse_denovo_gene_sets_config(
    config: dict[str, Any],
) -> DenovoGeneSetsConfig | None:
    """Parse de novo gene sets configuration."""
    enabled = config.get("enabled", False)
    if not enabled:
        return None
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
            name: parse_recurrency_criteria(name, criteria)
            for name, criteria in criteria_segments.items()
        }

    gene_sets_ids = _validate_gene_sets_ids(
        config.get("gene_sets_names", []),
        effect_types=effect_types,
        sexes=sexes,
        recurrency=recurrency,
    )
    if not gene_sets_ids:
        raise ValueError("No gene sets ids defined in denovo gene sets config")

    return DenovoGeneSetsConfig(
        enabled=enabled,
        selected_person_set_collections=selected_person_set_collections,
        effect_types=effect_types,
        sexes=sexes,
        recurrency=recurrency,
        gene_sets_ids=gene_sets_ids,
    )


def parse_denovo_gene_sets_study_config(
    study_config: dict[str, Any],
) -> DenovoGeneSetsConfig | None:
    """Parse de novo gene sets study configuration."""
    denovo_gene_sets_config = study_config.get("denovo_gene_sets", {})
    if not denovo_gene_sets_config:
        return None
    return parse_denovo_gene_sets_config(denovo_gene_sets_config)


class DGSSpec(BaseModel):
    """De novo gene set specification."""

    model_config = ConfigDict(extra="forbid")

    gene_set_id: str
    criterias: dict[
        str,
        EffectsCriteria | SexesCriteria | RecurrencyCriteria,
    ]

    def _str_(self) -> str:
        return self.gene_set_id


def create_denovo_gene_set_spec(
    gene_set_id: str,
    config: DenovoGeneSetsConfig,
) -> DGSSpec:
    """Create de novo gene set specification from name."""
    segments = gene_set_id.split(".")
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
    return DGSSpec(
        gene_set_id=gene_set_id,
        criterias=criterias,
    )


class DGSCQuery(BaseModel):
    """Query for de novo gene set collection."""

    model_config = ConfigDict(extra="forbid")

    gene_set_id: str
    psc_id: str
    selected_person_sets: set[str]

    effects: list[EffectsCriteria]
    sex: list[SexesCriteria]
    recurrency: RecurrencyCriteria | None

    def _str_(self) -> str:
        return (
            f"{self.gene_set_id} {self.psc_id}:"
            f"{','.join(self.selected_person_sets)}"
        )


def parse_dgsc_query(
    gene_set_spec: str,
    dgsc_config: DenovoGeneSetsConfig,
) -> DGSCQuery:
    """Parse de novo gene set collection query."""
    gene_set_id, other = gene_set_spec.split(" ")
    if gene_set_id not in dgsc_config.gene_sets_ids:
        raise ValueError(f"Invalid gene set id: {gene_set_id}")
    psc_id, other = other.split(":")
    if psc_id not in dgsc_config.selected_person_set_collections:
        raise ValueError(f"Invalid person set collection id: {psc_id}")
    person_sets = other.split(",")

    segments = gene_set_id.split(".")
    effect: list[EffectsCriteria] = []
    sex: list[SexesCriteria] = []
    recurrency: RecurrencyCriteria | None = None

    for segment in segments:
        if segment in dgsc_config.effect_types:
            effect = [dgsc_config.effect_types[segment]]
            continue
        if segment in dgsc_config.sexes:
            sex = [dgsc_config.sexes[segment]]
            continue
        if segment in dgsc_config.recurrency:
            recurrency = dgsc_config.recurrency[segment]
            continue
        raise ValueError(f"Invalid segment: {segment}")

    return DGSCQuery(
        gene_set_id=gene_set_id,
        psc_id=psc_id,
        selected_person_sets=set(person_sets),
        effects=effect or list(dgsc_config.effect_types.values()),
        sex=sex or list(dgsc_config.sexes.values()),
        recurrency=recurrency,
    )
