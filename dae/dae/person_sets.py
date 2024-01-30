"""
Provide classes for grouping of individuals by some criteria.

This module provides functionality for grouping
individuals from a study or study group into various
sets based on what value they have in a given mapping.
"""
from __future__ import annotations
from dataclasses import dataclass
import logging

from typing import Optional, Any, FrozenSet, Generator, cast
from box import Box

from dae.variants.attributes import Sex
from dae.pedigrees.family import Person
from dae.pedigrees.families_data import FamiliesData
from dae.pheno.pheno_data import PhenotypeData, MeasureType


logger = logging.getLogger(__name__)


@dataclass
class ChildrenStats:
    """Statistics about children in a PersonSet."""

    male: int
    female: int
    unspecified: int

    @property
    def total(self) -> int:
        return self.male + self.female + self.unspecified


@dataclass
class ChildrenBySex:
    """Statistics about children in a PersonSet."""

    male: set[tuple[str, str]]
    female: set[tuple[str, str]]
    unspecified: set[tuple[str, str]]


@dataclass
class PersonSet:
    """Set of individuals mapped to a common value in the source."""

    def __init__(
            self, psid: str, name: str,
            values: list[str], color: str,
            persons: dict[tuple[str, str], Person]):
        self.id: str = psid  # pylint: disable=invalid-name
        self.name: str = name
        self.values: list[str] = values
        self.color: str = color
        assert all(not p.generated for p in persons.values())
        self.persons: dict[tuple[str, str], Person] = persons
        self._children_by_sex: Optional[ChildrenBySex] = None
        self._children_stats: Optional[ChildrenStats] = None

    def __repr__(self) -> str:
        return f"PersonSet({self.id}: {self.name}, {len(self.persons)})"

    def __len__(self) -> int:
        return len(self.persons)

    def get_children(self) -> Generator[Person, None, None]:
        for person in self.persons.values():
            if person.is_child():
                yield person

    def get_children_by_sex(self) -> ChildrenBySex:
        """Return all children in the person set splitted by sex."""
        if self._children_by_sex is None:
            self._children_by_sex = ChildrenBySex(
                set(), set(), set()
            )
            for child in self.get_children():
                if child.sex == Sex.M:
                    self._children_by_sex.male.add(child.fpid)
                elif child.sex == Sex.F:
                    self._children_by_sex.female.add(child.fpid)
                else:
                    assert child.sex == Sex.U
                    self._children_by_sex.unspecified.add(child.fpid)

        assert self._children_by_sex is not None
        return self._children_by_sex

    def get_children_stats(self) -> ChildrenStats:
        """Return statistics about children in the person set."""
        if self._children_stats is None:
            children_by_sex = self.get_children_by_sex()
            self._children_stats = ChildrenStats(
                len(children_by_sex.male),
                len(children_by_sex.female),
                len(children_by_sex.unspecified)
            )
        assert self._children_stats is not None
        return self._children_stats

    def get_parents(self) -> Generator[Person, None, None]:
        for person in self.persons.values():
            if person.is_parent():
                yield person

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "values": self.values,
            "color": self.color,
            "person_ids": list(self.persons.keys())
        }

    @staticmethod
    def from_json(json: dict[str, Any], families: FamiliesData) -> PersonSet:
        """Construct person set from a JSON dict."""
        real_persons = families.real_persons
        persons = {
            pid: real_persons[pid]
            for pid in json["person_ids"] if pid in real_persons
        }
        return PersonSet(
            json["id"],
            json["name"],
            json["values"],
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
            self, pscid: str, name: str,
            config: dict[str, Any],
            sources: list[Source],
            person_sets: dict[str, PersonSet],
            default: PersonSet,
            families: FamiliesData):

        assert config.get("default") is not None

        self.id: str = pscid  # pylint: disable=invalid-name
        self.name: str = name
        self.config = config
        self.sources = sources

        self.person_sets: dict[str, PersonSet] = person_sets
        self.default: PersonSet = default

        self.person_sets[default.id] = default

        self.families: FamiliesData = families

    def __repr__(self) -> str:
        return f"PersonSetCollection({self.id}: {self.person_sets})"

    def __len__(self) -> int:
        return len(self.person_sets)

    def is_pedigree_only(self) -> bool:
        return all(s.sfrom == "pedigree" for s in self.sources)

    @staticmethod
    def _sources_from_config(
        person_set_collection: dict[str, Any]
    ) -> list[Source]:
        sources = [
            PersonSetCollection.Source(src["from"], src["source"])
            for src in person_set_collection["sources"]
        ]
        return sources

    @staticmethod
    def _produce_sets(config: dict[str, Any]) -> dict[str, PersonSet]:
        """
        Produce initial PersonSet instances.

        Initializes a dictionary of person set IDs mapped to
        empty PersonSet instances from a given configuration.
        """
        person_set_configs = config["domain"]
        result = {}
        for person_set in person_set_configs:
            result[person_set["id"]] = PersonSet(
                person_set["id"],
                person_set["name"],
                person_set["values"],
                person_set["color"],
                {},
            )
        return result

    @staticmethod
    def _produce_default_person_set(config: dict[str, Any]) -> PersonSet:
        assert config["default"] is not None, config

        default_config = config["default"]
        return PersonSet(
            default_config["id"],
            default_config["name"],
            [],
            default_config["color"],
            {},
        )

    @staticmethod
    def get_person_color(
        person: Person, person_set_collection: PersonSetCollection
    ) -> str:
        """Get the hex color value for a Person in a PersonSetCollection."""
        if person.generated:
            return "#E0E0E0"

        if person_set_collection is None:
            return "#FFFFFF"

        matching_person_set = person_set_collection.get_person_set_of_person(
            person.fpid
        )
        if matching_person_set is not None:
            return matching_person_set.color

        logger.warning(
            "Person <%s> could not be found in any"
            " domain of <%s>!",
            person.fpid, person_set_collection.id
        )
        return "#AAAAAA"

    @staticmethod
    def remove_empty_person_sets(
        person_set_collection: PersonSetCollection
    ) -> PersonSetCollection:
        """Remove all empty person sets in a PersonSetCollection in place."""
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

    def collect_person_collection_attributes(
        self, person: Person, pheno_db: Optional[PhenotypeData]
    ) -> FrozenSet[str]:
        """Collect all configured attributes for a Person."""
        values = []
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

                pheno_values = list(pheno_db.get_people_measure_values(
                    [source.ssource],
                    person_ids=[person.person_id],
                ))
                if len(pheno_values) == 0:
                    value = None
                else:
                    value = pheno_values[0][source.ssource]
            else:
                raise ValueError(f"Invalid source type {source.sfrom}!")
            values.append(value)

        # make unified frozenset value
        return frozenset(values)

    @staticmethod
    def from_families(
        psc_config: dict[str, Any],
        families_data: FamiliesData,
        pheno_db: Optional[PhenotypeData] = None
    ) -> PersonSetCollection:
        """Produce a PersonSetCollection from a config and pedigree."""
        collection = PersonSetCollection(
            psc_config["id"],
            psc_config["name"],
            psc_config,
            PersonSetCollection._sources_from_config(psc_config),
            PersonSetCollection._produce_sets(psc_config),
            PersonSetCollection._produce_default_person_set(psc_config),
            families_data,
        )
        value_to_id = {
            frozenset(ps_config["values"]): ps_config["id"]
            for ps_config in psc_config["domain"]
        }
        logger.debug("person set collection value_to_id: %s", value_to_id)
        for person_id, person in families_data.real_persons.items():
            assert not person.missing
            value = collection.collect_person_collection_attributes(
                person, pheno_db)
            if value not in value_to_id:
                collection.default.persons[person_id] = person
            else:
                set_id = value_to_id[value]
                collection.person_sets[set_id].persons[person_id] = person

        return PersonSetCollection.remove_empty_person_sets(collection)

    @staticmethod
    def merge_configs(
        person_set_collections: list[PersonSetCollection]
    ) -> Box:
        """
        Merge the configurations of a list of PersonSetCollection objects.

        Only supports merging PersonSetCollection objects with matching ids.
        The method will not merge the PersonSet objects' values.
        """
        assert len(person_set_collections) > 0
        collections_iterator = iter(person_set_collections)
        first = next(collections_iterator)

        result: dict[str, Any] = {}
        result["id"] = first.id
        result["name"] = first.name

        sources = [{
            "from": "pedigree",
            "source": first.id
        }]
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
                    # check if this person set is compatible
                    # with the existing one
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

        return Box(result)

    def get_person_set(
        self, person_id: tuple[str, str]
    ) -> Optional[PersonSet]:
        for person_set in self.person_sets.values():
            if person_id in person_set.persons:
                return person_set
        return None

    def get_person_set_of_person(
        self, fpid: tuple[str, str]
    ) -> Optional[PersonSet]:
        """Retrieve the PersonSet associated with the given person identifier.

        Args:
            fpid (tuple[str, str]): The person identifier consisting of two
                strings - family ID and person ID.

        Returns:
            Optional[PersonSet]: The PersonSet associated with the given
                person identifier, or None if not found.
        """
        result = self.get_person_set(fpid)
        if result is not None:
            return result
        return None

    @staticmethod
    def combine(
        collections: list[PersonSetCollection],
        families: FamiliesData
    ) -> PersonSetCollection:
        """Combine a list of PersonSetCollection objects into a single one."""
        if len(collections) == 0:
            raise ValueError("can't combine empty list of collections")
        if len(collections) == 1:
            return collections[0]

        config = PersonSetCollection.merge_configs(collections)
        result = PersonSetCollection(
            config["id"], config["name"], config,
            PersonSetCollection._sources_from_config(config),
            PersonSetCollection._produce_sets(config),
            PersonSetCollection._produce_default_person_set(config),
            families)

        for person_id, person in families.real_persons.items():
            person_set = None
            for psc in collections:
                person_set = psc.get_person_set(person_id)
                if person_set is not None:
                    break
            if person_set is not None:
                result.person_sets[person_set.id].persons[person_id] = person
            else:
                result.default.persons[person_id] = person

        return PersonSetCollection.remove_empty_person_sets(result)

    def config_json(self) -> dict[str, Any]:
        """Produce a JSON configuration for this PersonSetCollection object."""
        domain = []
        for person_set in self.person_sets.values():
            if self.default.id == person_set.id:
                continue
            domain.append({
                "id": person_set.id,
                "name": person_set.name,
                "values": person_set.values,
                "color": person_set.color,
            })
        sources = [
            {"from": s.sfrom, "source": s.ssource}
            for s in self.sources
        ]
        conf = {
            "id": self.id,
            "name": self.name,
            "sources": sources,
            "domain": domain,
            "default": {
                "id": self.default.id,
                "name": self.default.name,
                "color": self.default.color,
            }
        }

        return conf

    def domain_json(self) -> dict[str, Any]:
        """Produce a JSON to represent domain of this PersonSetCollection."""
        domain = []
        for person_set in self.person_sets.values():
            domain.append({
                "id": person_set.id,
                "name": person_set.name,
                "color": person_set.color,
            })
        conf = {
            "id": self.id,
            "name": self.name,
            "domain": domain,
        }

        return conf

    def get_stats(self) -> dict[str, dict[str, int]]:
        """
        Return a dictionary with statistics for each PersonSet.

        The statistics are a dictionary containing the amount of parents
        and children in the set.
        """
        result = {}
        for set_id, person_set in self.person_sets.items():
            parents = len(list(person_set.get_parents()))
            children = len(list(person_set.get_children()))
            result[set_id] = {
                "parents": parents,
                "children": children,
            }
        return result

    def to_json(self) -> dict[str, Any]:
        """Serialize a person sets collection to a json format."""
        return {
            "config": self.config_json(),
            "person_sets": [
                ps.to_json() for ps in self.person_sets.values()
            ]
        }

    @staticmethod
    def from_json(
        data: dict[str, Any], families: FamiliesData
    ) -> PersonSetCollection:
        """Construct person sets collection from json serialization."""
        config = data["config"]

        psc = PersonSetCollection(
            config["id"],
            config["name"],
            config,
            PersonSetCollection._sources_from_config(config),
            PersonSetCollection._produce_sets(config),
            PersonSetCollection._produce_default_person_set(config),
            families,
        )
        for ps_json in data["person_sets"]:
            person_set = psc.person_sets[ps_json["id"]]
            for fpid_json in ps_json["person_ids"]:
                fpid = cast(tuple[str, str], tuple(fpid_json))
                person = families.persons[fpid]
                assert person.get_attr(psc.id) == person_set.id
                person_set.persons[fpid] = person

        PersonSetCollection.remove_empty_person_sets(psc)
        return psc


@dataclass
class PSCQuery:
    """Person set collection query."""

    collection_id: str
    selected_person_sets: set[str]
