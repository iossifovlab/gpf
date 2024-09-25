from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
)


class DefaultPersonSetConfig(BaseModel):
    """Default configuration for a person set."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    color: str


class PersonSetConfig(BaseModel):
    """Configuration for a person set."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    values: tuple[str]
    color: str


class SourceConfig(BaseModel):
    """Configuration for a source."""

    model_config = ConfigDict(extra="forbid")

    from_: Literal["pedigree", "pheno_db"]
    source: str


class PersonSetsCollectionConfig(BaseModel):
    """Configuration for a collection of person sets."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    sources: list[SourceConfig]
    domain: list[PersonSetConfig]
    default: DefaultPersonSetConfig


def _parse_psc_sources(
    psc_id: str,
    psc_config: dict[str, Any],
) -> list[SourceConfig]:
    if "sources" not in psc_config:
        raise ValueError(
            f"No sources defined for person set: {psc_id}")
    psc_sources = []
    for source in psc_config["sources"]:
        if "from" not in source:
            raise ValueError(
                f"No from defined for source in person set: {psc_id}")
        if "source" not in source:
            raise ValueError(
                f"No source defined for source in person set: {psc_id}")
        psc_sources.append(SourceConfig(from_=source["from"],
                                        source=source["source"]))
    return psc_sources


def _parse_psc_domain(
    psc_id: str,
    psc_config: dict[str, Any],
) -> list[PersonSetConfig]:
    if "domain" not in psc_config:
        raise ValueError(
            f"No domain defined for person set collection: {psc_id}")
    psc_domain = []
    for domain in psc_config["domain"]:
        if "id" not in domain:
            raise ValueError(
                f"No id defined for domain in person set collection: "
                f"{psc_id}")
        if "name" not in domain:
            raise ValueError(
                f"No name defined for domain in person set collection: "
                f"{psc_id}")
        if "values" not in domain:
            raise ValueError(
                f"No values defined for domain in person set collection: "
                f"{psc_id}")
        if "color" not in domain:
            raise ValueError(
                f"No color defined for domain in person set collection: "
                f"{psc_id}")

        psc_domain.append(PersonSetConfig(
            id=domain["id"],
            name=domain["name"],
            values=tuple(domain["values"]),
            color=domain["color"],
        ))
    return psc_domain


def _parse_psc_default(
    psc_id: str,
    psc_config: dict[str, Any],
) -> DefaultPersonSetConfig:
    if "default" not in psc_config:
        raise ValueError(
            f"No default defined for person set collection: {psc_id}")
    psc_default = psc_config["default"]
    if "id" not in psc_default:
        raise ValueError(
            f"No id defined for default in person set collection: {psc_id}")
    if "name" not in psc_default:
        raise ValueError(
            f"No name defined for default in person set collection: {psc_id}")
    if "color" not in psc_default:
        raise ValueError(
            f"No color defined for default in person set collection: {psc_id}")
    return DefaultPersonSetConfig(
        id=psc_default["id"],
        name=psc_default["name"],
        color=psc_default["color"],
    )


def parse_person_sets_collection_config(
    config: dict[str, Any],
) -> dict[str, PersonSetsCollectionConfig]:
    """Parse a person sets configuration."""
    if "person_set_collections" not in config:
        raise ValueError("Invalid person sets collections configuration")
    pscs_config = config["person_set_collections"]
    if "selected_person_set_collections" not in pscs_config:
        raise ValueError("No person set collections selected")

    psc_selected = pscs_config["selected_person_set_collections"]
    result = {}
    for psc_id in psc_selected:
        if psc_id not in pscs_config:
            raise ValueError(
                f"Selected person set collection not found: {psc_id}")
        psc_config = pscs_config[psc_id]
        if "id" not in psc_config:
            raise ValueError(
                f"No id defined for person set collection: {psc_id}")
        if "name" not in psc_config:
            raise ValueError(
                f"No name defined for person set collection: {psc_id}")
        if psc_config["id"] != psc_id:
            raise ValueError(
                f"Person set collection id mismatch: {psc_id} != "
                f"{psc_config['id']}")

        psc_sources = _parse_psc_sources(psc_id, psc_config)
        psc_domain = _parse_psc_domain(psc_id, psc_config)
        psc_default = _parse_psc_default(psc_id, psc_config)

        result[psc_id] = PersonSetsCollectionConfig(
            id=psc_id,
            name=psc_config["name"],
            sources=psc_sources,
            domain=psc_domain,
            default=psc_default,
        )
    return result
