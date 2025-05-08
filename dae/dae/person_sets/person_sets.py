"""
Provide classes for grouping of individuals by some criteria.

This module provides functionality for grouping
individuals from a study or study group into various
sets based on what value they have in a given mapping.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
)

from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import Person
from dae.variants.attributes import Sex

logger = logging.getLogger(__name__)


class PersonSetConfig(BaseModel):
    """Configuration for a person set."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    values: tuple[str, ...]
    color: str


class SourceConfig(BaseModel):
    """Configuration for a source."""

    model_config = ConfigDict(extra="forbid")

    from_: Literal["pedigree", "phenodb"]
    source: str


class PersonSetCollectionConfig(BaseModel):
    """Configuration for a collection of person sets."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    sources: list[SourceConfig]
    domain: list[PersonSetConfig]
    default: PersonSetConfig


def _parse_psc_sources(
    psc_id: str,
    psc_config: dict[str, Any],
) -> list[SourceConfig]:
    if "sources" not in psc_config:
        raise ValueError(
            f"No sources defined for person set collection: {psc_id}")
    psc_sources = []
    for source in psc_config["sources"]:
        if "from" not in source:
            raise ValueError(
                f"No 'from' defined for source in person set collection: "
                f"{psc_id}")
        if "source" not in source:
            raise ValueError(
                f"No 'source' defined for source in person set collection: "
                f"{psc_id}")
        psc_sources.append(SourceConfig(from_=source["from"],
                                        source=source["source"]))
    if not psc_sources:
        raise ValueError(
            f"Empty sources defined for person set collection: {psc_id}")
    return psc_sources


def parse_person_set_config(
    psc_id: str,
    domain: dict[str, Any],
) -> PersonSetConfig:
    """Parse a person set configuration."""
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
    return PersonSetConfig(
        id=domain["id"],
        name=domain["name"],
        values=tuple(domain["values"]),
        color=domain["color"],
    )


def _parse_psc_domain(
    psc_id: str,
    psc_config: dict[str, Any],
    psc_sources: list[SourceConfig],
) -> list[PersonSetConfig]:
    if "domain" not in psc_config:
        raise ValueError(
            f"No domain defined for person set collection: {psc_id}")
    psc_domain = []
    for domain in psc_config["domain"]:
        ps_config = parse_person_set_config(psc_id, domain)
        if len(ps_config.values) != len(psc_sources):
            raise ValueError(
                f"Values count {ps_config.values} "
                "mismatch for domain in person set collection: "
                f"{psc_id}")
        psc_domain.append(ps_config)

    if not psc_domain:
        logger.warning(
            "Empty domain defined for person set collection: %s", psc_id)
    return psc_domain


def _parse_psc_default(
    psc_id: str,
    psc_config: dict[str, Any],
) -> PersonSetConfig:
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
    if "values" in psc_default:
        raise ValueError(
            f"Values shoud not be defined for default in "
            f"person set collection: {psc_id}")

    return PersonSetConfig(
        values=(),
        **psc_default,
    )


def parse_person_set_collection_config(
    psc_config: dict[str, Any],
) -> PersonSetCollectionConfig:
    """Parse a person set collection configuration."""
    if "id" not in psc_config:
        raise ValueError(
            "No id defined for person set collection configuration")

    psc_id = psc_config["id"]
    if "name" not in psc_config:
        raise ValueError(
            f"No name defined for person set collection: {psc_id}")
    if psc_config["id"] != psc_id:
        raise ValueError(
            f"Person set collection id mismatch: {psc_id} != "
            f"{psc_config['id']}")

    psc_sources = _parse_psc_sources(psc_id, psc_config)
    psc_domain = _parse_psc_domain(psc_id, psc_config, psc_sources)
    psc_default = _parse_psc_default(psc_id, psc_config)

    return PersonSetCollectionConfig(
        id=psc_id,
        name=psc_config["name"],
        sources=psc_sources,
        domain=psc_domain,
        default=psc_default,
    )


def parse_person_set_collections_study_config(
    config: dict[str, Any],
) -> dict[str, PersonSetCollectionConfig]:
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

        psc_config = parse_person_set_collection_config(psc_config)
        result[psc_id] = psc_config
    return result


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
            values: tuple[str, ...], color: str,
            persons: dict[tuple[str, str], Person]):
        self.id: str = psid  # pylint: disable=invalid-name
        self.name: str = name
        self.values: tuple[str, ...] = values
        self.color: str = color
        assert all(not p.generated for p in persons.values())
        self.persons: dict[tuple[str, str], Person] = persons
        self._children_by_sex: ChildrenBySex | None = None
        self._children_stats: ChildrenStats | None = None
        self._children: list[Person] | None = None
        self._children_count: int | None = None

    def __repr__(self) -> str:
        return f"PersonSet({self.id}: {self.name}, {len(self.persons)})"

    def __len__(self) -> int:
        return len(self.persons)

    def get_children(self) -> list[Person]:
        """Return all children in the person set."""
        if self._children is None:
            self._children = []
            for person in self.persons.values():
                if person.is_child:
                    self._children.append(person)
        return self._children

    def get_children_count(self) -> int:
        if self._children_count is None:
            self._children_count = len(self.get_children())
        return self._children_count

    def get_children_by_sex(self) -> ChildrenBySex:
        """Return all children in the person set splitted by sex."""
        if self._children_by_sex is None:
            self._children_by_sex = ChildrenBySex(
                set(), set(), set(),
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
                len(children_by_sex.unspecified),
            )
        assert self._children_stats is not None
        return self._children_stats

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "values": self.values,
            "color": self.color,
            "person_ids": list(self.persons.keys()),
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
            persons,
        )


@dataclass
class PSCQuery:
    """Person set collection query."""

    psc_id: str
    selected_person_sets: set[str]


class PersonSetCollection:
    """The collection of all possible person sets in a given source."""

    def __init__(
            self,
            config: PersonSetCollectionConfig,
            person_sets: dict[str, PersonSet],
            default: PersonSet,
            families: FamiliesData):

        self.config = config
        self.id: str = config.id
        self.name: str = config.name
        self.sources = self.config.sources

        self.person_sets: dict[str, PersonSet] = person_sets
        self.default: PersonSet = default

        self.person_sets[default.id] = default

        self.families: FamiliesData = families

    def __repr__(self) -> str:
        return f"PersonSetCollection({self.id}: {self.person_sets})"

    def __len__(self) -> int:
        return len(self.person_sets)

    def is_pedigree_only(self) -> bool:
        return all(s.from_ == "pedigree" for s in self.sources)

    @staticmethod
    def _produce_sets(
        config: PersonSetCollectionConfig,
    ) -> dict[str, PersonSet]:
        """
        Produce initial PersonSet instances.

        Initializes a dictionary of person set IDs mapped to
        empty PersonSet instances from a given configuration.
        """
        result = {}
        for ps_config in config.domain:
            result[ps_config.id] = PersonSet(
                ps_config.id,
                name=ps_config.name,
                values=ps_config.values,
                color=ps_config.color,
                persons={},
            )
        return result

    @staticmethod
    def _produce_default_person_set(
        config: PersonSetCollectionConfig,
    ) -> PersonSet:
        default_config = config.default
        return PersonSet(
            default_config.id,
            name=default_config.name,
            values=(),
            color=default_config.color,
            persons={},
        )

    @staticmethod
    def get_person_color(
        person: Person,
        psc: PersonSetCollection | None,
    ) -> str:
        """Get the hex color value for a Person in a PersonSetCollection."""
        if person.generated:
            return "#E0E0E0"

        if psc is None:
            return "#FFFFFF"

        matching_person_set = psc.get_person_set_of_person(
            person.fpid,
        )
        if matching_person_set is not None:
            return matching_person_set.color

        logger.warning(
            "Person <%s> could not be found in any"
            " domain of <%s>!",
            person.fpid, psc.id,
        )
        return "#AAAAAA"

    @staticmethod
    def remove_empty_person_sets(
        person_set_collection: PersonSetCollection,
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
        self,
        person: Person,
        pheno_fetcher: Callable | None,
    ) -> tuple[str, ...]:
        """Collect all configured attributes for a Person."""
        values = []
        for source in self.sources:
            if source.from_ == "pedigree":
                value = person.get_attr(source.source)
                # Convert to string since some of the person's
                # attributes can be of an enum type
                if value is not None:
                    value = str(value)
            elif source.from_ == "phenodb" and pheno_fetcher is not None:
                pheno_values = list(pheno_fetcher(
                    [source.source],
                    person_ids=[person.person_id],
                ))
                if len(pheno_values) == 0:
                    value = None
                else:
                    value = pheno_values[0][source.source]
                    assert type(value) in {int, str}, (
                        f"Continuous measures not allowed in person sets! "
                        f"({source.source})")
            else:
                raise ValueError(f"Invalid source type {source.from_}!")
            values.append(value)

        return tuple(values)

    @staticmethod
    def from_families(
        psc_config: PersonSetCollectionConfig,
        families_data: FamiliesData,
        pheno_fetcher: Callable | None = None,
    ) -> PersonSetCollection:
        """Produce a PersonSetCollection from a config and pedigree."""
        collection = PersonSetCollection(
            psc_config,
            PersonSetCollection._produce_sets(psc_config),
            PersonSetCollection._produce_default_person_set(psc_config),
            families_data,
        )
        value_to_id = {
            ps_config.values: ps_config.id
            for ps_config in psc_config.domain
        }
        logger.debug("person set collection value_to_id: %s", value_to_id)
        for person_id, person in families_data.real_persons.items():
            assert not person.missing
            value = collection.collect_person_collection_attributes(
                person, pheno_fetcher)
            if value not in value_to_id:
                collection.default.persons[person_id] = person
            else:
                set_id = value_to_id[value]
                collection.person_sets[set_id].persons[person_id] = person

        return PersonSetCollection.remove_empty_person_sets(collection)

    @staticmethod
    def merge_configs(
        person_set_collections: list[PersonSetCollection],
    ) -> PersonSetCollectionConfig:
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
            "source": first.id,
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
                "color": person_set.color,
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
                        "color": person_set.color,
                    }
                    domain[person_set.id] = result_def

        if first.default.id in domain:
            del domain[first.default.id]

        result["domain"] = [
            domain[vid] for vid in sorted(domain.keys())
        ]

        return parse_person_set_collection_config(result)

    def get_person_set(
        self, person_id: tuple[str, str],
    ) -> PersonSet | None:
        for person_set in self.person_sets.values():
            if person_id in person_set.persons:
                return person_set
        return None

    def get_person_set_of_person(
        self, fpid: tuple[str, str],
    ) -> PersonSet | None:
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
        families: FamiliesData,
    ) -> PersonSetCollection:
        """Combine a list of PersonSetCollection objects into a single one."""
        if len(collections) == 0:
            raise ValueError("can't combine empty list of collections")
        if len(collections) == 1:
            return collections[0]

        config = PersonSetCollection.merge_configs(collections)
        result = PersonSetCollection(
            config,
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
            {"from": s.from_, "source": s.source}
            for s in self.sources
        ]
        return {
            "id": self.id,
            "name": self.name,
            "sources": sources,
            "domain": domain,
            "default": {
                "id": self.default.id,
                "name": self.default.name,
                "color": self.default.color,
            },
        }

    def legend_json(self) -> list[dict[str, Any]]:
        return [
            {
                "id": person_set.id,
                "name": person_set.name,
                "color": person_set.color,
            }
            for person_set in self.person_sets.values()
        ]

    def domain_json(self) -> dict[str, Any]:
        """Produce a JSON to represent domain of this PersonSetCollection."""
        domain = [
            {
                "id": person_set.id,
                "name": person_set.name,
                "color": person_set.color,
            }
            for person_set in self.person_sets.values()
        ]
        return {
            "id": self.id,
            "name": self.name,
            "domain": domain,
        }

    def get_stats(self) -> dict[str, dict[str, int]]:
        """
        Return a dictionary with statistics for each PersonSet.

        The statistics are a dictionary containing the amount of parents
        and children in the set.
        """
        result = {}
        for set_id, person_set in self.person_sets.items():
            children_stats = person_set.get_children_stats()
            children = children_stats.total
            result[set_id] = {
                "parents": 0,
                "children": children,
            }
        return result

    def query_fpids(self, query: PSCQuery) -> set[tuple[str, str]] | None:
        """Query the PersonSetCollection for the selected person sets."""
        if query.psc_id != self.id:
            raise ValueError(
                f"Query for PersonSetCollection {query.psc_id} "
                f"on PersonSetCollection {self.id}")
        all_person_sets = set(self.person_sets.keys())
        if all_person_sets & query.selected_person_sets == all_person_sets:
            # Everything is selected
            return None

        result: set[tuple[str, str]] = set()
        for set_id in query.selected_person_sets:
            if set_id not in self.person_sets:
                continue
            result.update(self.person_sets[set_id].persons.keys())
        return result

    def query_person_ids(self, query: PSCQuery) -> set[str] | None:
        """Query the PersonSetCollection for the selected person sets."""
        fpids = self.query_fpids(query)
        if fpids is None:
            return None
        return {fpid[1] for fpid in fpids}

    def _pedigree_query_selected_person_sets(self, query):
        selected_person_sets = set(query.selected_person_sets)
        available_person_sets = set(self.person_sets.keys())
        available_person_sets.add(self.default.id)
        unknown = query.selected_person_sets.difference(
            available_person_sets)

        if unknown:
            logger.info(
                "person set collection query contains unknown person sets: %s",
                unknown)
            selected_person_sets = selected_person_sets & available_person_sets
        return selected_person_sets

    def _pedigree_query_all_fields(self):
        return [
            source.source for source in self.config.sources
        ]

    def _pedigree_query_has_unsupported_fields(self) -> bool:
        supported_fields = {"sex", "role", "status"}

        unsupported_fields = set(
            self._pedigree_query_all_fields()).difference(supported_fields)
        if unsupported_fields:
            logger.info(
                "queries over pedigree field <%s> are not supported",
                unsupported_fields)
            return True
        return False

    def _pedigree_query_all_values(self) -> dict[str, list[str]]:
        result = defaultdict(list)
        for psc in self.config.domain:
            for field, value in zip(
                    self._pedigree_query_all_fields(),
                    psc.values,
                    strict=True):
                result[field].append(value)
        return result

    def _pedigree_query_check_multi_field_multi_value(
            self, result, default_result,
        ) -> bool:
        if len(result) + len(default_result) > 1:
            multi_values_count = 0
            for values in result.values():
                if len(values) > 1:
                    multi_values_count += 1
            for values in default_result.values():
                if len(values) > 1:
                    multi_values_count += 1
            return multi_values_count > 1

        return False

    def _pedigree_query_map_queries(
        self, result_query: dict[str, str],
    ) -> dict[str, str]:
        field_to_query = {
            "sex": "sexes",
            "role": "roles",
            "status": "affected_statuses",
        }
        return {
            field_to_query[field]: query
            for field, query in result_query.items()
        }

    def transform_pedigree_queries(
        self, query: PSCQuery,
    ) -> dict[str, str] | None:
        """Transform person set collection query into query variants."""
        if query.psc_id != self.id:
            raise ValueError(
                f"Query for PersonSetCollection {query.psc_id} "
                f"on PersonSetCollection {self.id}")
        if not self.is_pedigree_only():
            return None
        selected_person_sets = self._pedigree_query_selected_person_sets(query)
        if not selected_person_sets:
            return {}

        if self._pedigree_query_has_unsupported_fields():
            return None

        result = defaultdict(set)
        default_result = defaultdict(set)

        for ps_id in selected_person_sets:
            if ps_id == self.default.id:
                # handle default person set
                for field, values in self._pedigree_query_all_values().items():
                    default_result[field].update(values)
                continue
            for field, value in zip(
                    [s.source for s in self.config.sources],
                    self.person_sets[ps_id].values,
                    strict=True):
                result[field].add(str(value))

        # Since we alwayes do OR between queries on differenc fields we
        # can't support fully queries that use multiple on multiple fields
        if self._pedigree_query_check_multi_field_multi_value(
                result, default_result):
            return None

        default_queries = {
            field: " and ".join([f"(not {v})" for v in sorted(values)])
            for field, values in default_result.items()
        }
        result_queries = {}
        for field, values in result.items():
            temp = f"any([{','.join(sorted(values))}])"
            if field not in default_queries:
                result_queries[field] = temp
            else:
                result_queries[field] = f"{temp} or ({default_queries[field]})"
        for field, value in default_queries.items():
            if field not in result_queries:
                result_queries[field] = f"({value})"
        return self._pedigree_query_map_queries(result_queries)
