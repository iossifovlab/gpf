# pylint: disable=W0621,C0114,C0116,W0212,W0613
import re
import textwrap

import pytest
import toml
from dae.person_sets import (
    parse_person_set_collections_study_config,
)


@pytest.fixture
def person_set_collection_config() -> dict:
    content = textwrap.dedent(
        """
        [person_set_collections]
        selected_person_set_collections = ["status"]
        status.id = "status"
        status.name = "Affected Status"
        status.sources = [{ from = "pedigree", source = "status" }]
        status.domain = [
            {
                id = "unaffected",
                name = "Unaffected",
                values = ["unaffected"],
                color = "#ffffff"
            },
        ]
        status.default = {id = "unknown",name = "Unknown",color = "#aaaaaa"}

        """)

    return toml.loads(content)


def test_parse_person_set_collection_config_toml(
    person_set_collection_config: dict,
) -> None:
    config = person_set_collection_config
    assert config is not None

    psc_configs = parse_person_set_collections_study_config(config)
    assert psc_configs is not None
    assert len(psc_configs) == 1

    psc_config = psc_configs["status"]
    assert psc_config.id == "status"
    assert psc_config.name == "Affected Status"
    assert len(psc_config.sources) == 1
    assert psc_config.sources[0].from_ == "pedigree"
    assert psc_config.sources[0].source == "status"
    assert len(psc_config.domain) == 1
    assert psc_config.domain[0].id == "unaffected"
    assert psc_config.domain[0].name == "Unaffected"
    assert psc_config.domain[0].values == ("unaffected",)  # noqa: PD011


@pytest.mark.parametrize("to_delete, match_message", [
    (["person_set_collections", "selected_person_set_collections"],
      "No person set collections selected"),
    (["person_set_collections", "status", "id"],
      "No id defined for person set collection: status"),
    (["person_set_collections", "status", "name"],
      "No name defined for person set collection: status"),
    (["person_set_collections", "status", "sources"],
      "No sources defined for person set collection: status"),
    (["person_set_collections", "status", "domain"],
      "No domain defined for person set collection: status"),
    (["person_set_collections", "status", "default"],
      "No default defined for person set collection: status"),
])
def test_parse_person_set_collection_config_missing_keys(
    person_set_collection_config: dict,
    to_delete: list[str],
    match_message: str,
) -> None:
    config = person_set_collection_config
    sub = config
    for key in to_delete[:-1]:
        sub = sub[key]
    del sub[to_delete[-1]]

    with pytest.raises(ValueError, match=match_message):
        parse_person_set_collections_study_config(config)


@pytest.mark.parametrize("sources, match_message", [
    ([], "Empty sources defined for person set collection: status"),
    ([{"from": "pedigree"}],
     "No 'source' defined for source in person set collection: status"),
    ([{"sources": "status"}],
     "No 'from' defined for source in person set collection: status"),
])
def test_parse_person_set_collection_config_broken_sources(
    person_set_collection_config: dict,
    sources: list[dict],
    match_message: str,
) -> None:
    config = person_set_collection_config
    config["person_set_collections"]["status"]["sources"] = sources

    with pytest.raises(ValueError, match=match_message):
        parse_person_set_collections_study_config(config)


@pytest.mark.parametrize("domain, match_message", [
    ([{"id": "unaffected", "name": "Unaffected"}],
     "No values defined for domain in person set collection: status"),
    ([{"id": "unaffected", "name": "Unaffected", "values": ["unaffected"]}],
     "No color defined for domain in person set collection: status"),
    ([{"name": "Unaffected", "values": ["unaffected"]}],
     "No id defined for domain in person set collection: status"),
    ([{"id": "unaffected", "name": "Unaffected", "color": "#ffffff",
       "values": ["unaffected", "aaaa"]}],
     "Values count ('unaffected', 'aaaa') mismatch for domain in person set "
     "collection: status"),
])
def test_parse_person_set_collection_config_broken_domain(
    person_set_collection_config: dict,
    domain: list[dict],
    match_message: str,
) -> None:
    config = person_set_collection_config
    config["person_set_collections"]["status"]["domain"] = domain

    with pytest.raises(ValueError, match=re.escape(match_message)):
        parse_person_set_collections_study_config(config)


@pytest.mark.parametrize("default, match_message", [
    ({}, "No id defined for default in person set collection: status"),
    ({"id": "unspecified"},
     "No name defined for default in person set collection: status"),
    ({"id": "unspecified", "name": "Unspecified"},
     "No color defined for default in person set collection: status"),
    ({"id": "unspecified", "name": "Unspecified", "color": "#aaaaaa",
      "values": ["unspecified"]},
     "Values shoud not be defined for default in "
     "person set collection: status"),
])
def test_parse_person_set_collection_config_broken_default(
    person_set_collection_config: dict,
    default: dict,
    match_message: str,
) -> None:
    config = person_set_collection_config
    config["person_set_collections"]["status"]["default"] = default

    with pytest.raises(ValueError, match=re.escape(match_message)):
        parse_person_set_collections_study_config(config)
