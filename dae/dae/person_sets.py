"""This module provides functionality for grouping
individuals from a study or study group into various
sets based on what value they have in a given mapping.
"""
from __future__ import annotations
from dataclasses import dataclass

import logging

from typing import Dict, Set, Optional, Any, FrozenSet, List
from dae.configuration.gpf_config_parser import FrozenBox
from dae.pedigrees.family import Person, FamiliesData
from dae.pheno.pheno_db import PhenotypeData, MeasureType
from dae.variants.attributes import Role


logger = logging.getLogger(__name__)


@dataclass
class PersonSet:
    """A set of individuals which are all mapped to a
    common value in the source.
    """

    def __init__(
            self, psid: str, name: str,
            values: Set[str], color: str,
            persons: Dict[str, Person]):
        self.id: str = psid
        self.name: str = name
        self.values: Set[str] = values
        self.color: str = color
        self.persons: Dict[str, Person] = persons

    def __repr__(self):
        return f"PersonSet({self.id}: {self.name}, {len(self.persons)})"

    def get_persons_with_roles(self, *roles):
        for person in self.persons.values():
            if person.role in roles:
                yield person

    def get_children(self):
        for person in self.persons.values():
            if person.has_parent() and not person.generated:
                yield person

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "values": self.values,
            "color": self.color,
            "person_ids": list(self.persons.keys())
        }

    @staticmethod
    def from_json(json, families):
        persons = {
            pid: families.persons.get(pid) for pid in json["person_ids"]
        }
        return PersonSet(
            json["id"],
            json["name"],
            set(json["values"]),
            json["color"],
            persons
        )


class PersonSetCollection:
    """The collection of all possible person sets in a given source."""

    @dataclass(frozen=True, eq=True)
    class Source:
        sfrom: str
        ssource: str

    def __init__(
            self, pscid: str, name: str, config: FrozenBox,
            sources: Set[Source],
            person_sets: Dict[str, PersonSet],
            default: PersonSet,
            families: FamiliesData):

        assert config.get("default") is not None

        self.id: str = pscid
        self.name: str = name
        self.config = config
        self.sources = sources

        self.person_sets: Dict[str, PersonSet] = person_sets
        self.default: PersonSet = default

        self.person_sets[default.id] = default

        self.families: FamiliesData = families

    def __repr__(self):
        return f"PersonSetCollection({self.id}: {self.person_sets})"

    @staticmethod
    def _sources_from_config(person_set_collection) -> Set[Source]:
        sources = {
            PersonSetCollection.Source(src["from"], src["source"])
            for src in person_set_collection["sources"]
        }
        return sources

    @staticmethod
    def _produce_sets(config: FrozenBox) -> Dict[str, PersonSet]:
        """Initializes a dictionary of person set IDs
        mapped to empty PersonSet instances from a given configuration.
        """
        person_set_configs = [*config.domain]
        result = dict()
        for person_set in person_set_configs:
            result[person_set.id] = PersonSet(
                person_set.id,
                person_set.name,
                set(person_set["values"]),
                person_set.color,
                dict(),
            )
        return result

    @staticmethod
    def _produce_default_person_set(config: FrozenBox) -> PersonSet:
        assert config.default is not None, config

        return PersonSet(
            config.default.id,
            config.default.name,
            {"DEFAULT"},
            config.default.color,
            dict(),
        )

    @staticmethod
    def get_person_color(
            person: Person, person_set_collection: PersonSetCollection) -> str:

        if person.generated:
            return "#E0E0E0"

        if person_set_collection is None:
            return "#FFFFFF"

        matching_person_set = person_set_collection.get_person_set_of_person(
            person.person_id
        )
        if matching_person_set is not None:
            return matching_person_set.color

        logger.warning(
            f"Person '{person.person_id}' could not be found in any"
            f" domain of '{person_set_collection.id}'!"
        )
        return "#AAAAAA"

    @staticmethod
    def remove_empty_person_sets(
            person_set_collection: PersonSetCollection) -> PersonSetCollection:
        empty_person_sets = set()
        for set_id, person_set in person_set_collection.person_sets.items():
            if len(person_set.persons) == 0:
                empty_person_sets.add(set_id)
        logger.debug(
            "empty person sets to remove from  person set collection <%s>: %s",
            person_set_collection.id, empty_person_sets)

        for set_id in empty_person_sets:
            del person_set_collection.person_sets[set_id]
        return person_set_collection

    def _collect_person_collection_attributes(
            self, person: Person,
            pheno_db: Optional[PhenotypeData]) -> FrozenSet[str]:

        values = list()
        for source in self.sources:
            if source.sfrom == "pedigree":
                value = person.get_attr(source.ssource)
                # Convert to string since some of the person's
                # attributes can be of an enum type
                if value is not None:
                    value = str(value)
            elif source.sfrom == "phenodb" and pheno_db is not None:
                assert pheno_db.get_measure(source.ssource).measure_type \
                    in {MeasureType.categorical, MeasureType.ordinal}, \
                    f"Continuous measures not allowed in person sets! " \
                    f"({source.ssource})"

                pheno_values = pheno_db.get_values(
                    measure_ids=[source.ssource],
                    person_ids=[person.person_id],
                )
                value = pheno_values[person.person_id][source.ssource] \
                    if person.person_id in pheno_values else None
            else:
                raise ValueError(f"Invalid source type {source.sfrom}!")
            values.append(value)

        # make unified frozenset value
        return frozenset(values)

    @staticmethod
    def from_families(
            collection_config: FrozenBox,
            families_data: FamiliesData,
            pheno_db: Optional[PhenotypeData] = None) -> PersonSetCollection:

        """Produce a PersonSetCollection from its given configuration
        with a pedigree as its source.
        """
        collection = PersonSetCollection(
            collection_config.id,
            collection_config.name,
            collection_config,
            PersonSetCollection._sources_from_config(collection_config),
            PersonSetCollection._produce_sets(collection_config),
            PersonSetCollection._produce_default_person_set(collection_config),
            families_data,
        )
        value_to_id = {
            frozenset(person_set["values"]): person_set.id
            for person_set in collection_config.domain
        }

        for person_id, person in families_data.persons.items():
            value = collection._collect_person_collection_attributes(
                person, pheno_db)
            if value not in value_to_id:
                collection.default.persons[person_id] = person
            else:
                set_id = value_to_id[value]
                collection.person_sets[set_id].persons[person_id] = person

        return PersonSetCollection.remove_empty_person_sets(collection)

    @staticmethod
    def merge_configs(
            person_set_collections: List[PersonSetCollection]) -> FrozenBox:
        assert len(person_set_collections) > 0
        collections_iterator = iter(person_set_collections)
        first = next(collections_iterator)

        result: Dict[str, Any] = {}
        result["id"] = first.id
        result["name"] = first.name

        sources = []
        for source in first.sources:
            sources.append({
                "from": source.sfrom,
                "source": source.ssource
            })
        result["sources"] = sources

        result["default"] = {
            "id": first.default.id,
            "name": first.default.name,
            "color": first.default.color,
        }

        domain = {}
        for person_set in first.person_sets.values():
            result_def = {
                "id": person_set.id,
                "name": person_set.name,
                "values": list(person_set.values),
                "color": person_set.color
            }
            domain[person_set.id] = result_def

        for collection in collections_iterator:
            if result["id"] != collection.id:
                logger.error(
                    "trying to merge different type of collections: %s <-> %s",
                    collection.id, result["id"])
                raise ValueError(
                    "trying to merge different type of collections")
            for person_set in collection.person_sets.values():
                if person_set.id in domain:
                    pass
                else:
                    result_def = {
                        "id": person_set.id,
                        "name": person_set.name,
                        "values": list(person_set.values),
                        "color": person_set.color
                    }
                    domain[person_set.id] = result_def

        if first.default.id in domain:
            del domain[first.default.id]

        result["domain"] = [
            domain[vid] for vid in sorted(domain.keys())
        ]

        return FrozenBox(result)

    def get_person_set_of_person(self, person_id: str) -> PersonSet:
        for person_set in self.person_sets.values():
            if person_id in person_set.persons:
                return person_set
        raise ValueError(
            f"person {person_id} not in person set collection {self.id}")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "config": self.config,
            "person_sets": [ps.to_json() for ps in self.person_sets.values()],
            "default": self.default.to_json()
        }

    @staticmethod
    def from_json(config_json, families):
        config = FrozenBox(config_json)
        return PersonSetCollection.from_families(config, families)

    def get_stats(self):
        result = dict()
        for set_id, person_set in self.person_sets.items():
            parents = len(list(
                person_set.get_persons_with_roles(Role.dad, Role.mom)
            ))
            children = len(list(
                person_set.get_persons_with_roles(Role.prb, Role.sib)
            ))
            result[set_id] = {
                "parents": parents,
                "children": children,
            }
        return result
