# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import toml

from dae.person_sets.person_sets_config import (
    parse_person_sets_collection_config,
)


def test_parse_person_set_collection_config_toml() -> None:

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

    config = toml.loads(content)
    assert config is not None

    psc_configs = parse_person_sets_collection_config(config)
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
