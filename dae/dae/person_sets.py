"""This module provides functionality for grouping
individuals from a study or study group into various
sets based on what value they have in a given mapping.
"""

from typing import List, Dict, NamedTuple
from functools import reduce
from itertools import product

from dae.pedigrees.family import Person, FamiliesData


class PersonSet(NamedTuple):
    """A set of individuals which are all mapped to a
    common value in the source.
    """

    id: str
    name: str
    value: str
    color: str
    persons: Dict[str, Person]


class CompositePersonSet(NamedTuple):
    """A PersonSet whose persons satisfy multiple
    values from different sources.
    """

    id: str
    name: str
    values: List[str]
    color: str
    persons: Dict[str, Person]

    @staticmethod
    def compose(*person_sets, id=None, name="composite set", color="#FFFFFF"):
        # get the intersection of persons in the provided person sets
        key_intersection = reduce(
            lambda x, y: set(x.persons.keys()) & set(y.persons.keys()),
            person_sets,
        )
        common_persons = dict()
        for person_set in person_sets:
            for person_id in key_intersection:
                if person_id in person_set.persons:
                    common_persons[person_id] = person_set.persons[person_id]

        if id is None:
            id = ".".join([person_set.id for person_set in person_sets])

        values = [person_set.value for person_set in person_sets]

        return CompositePersonSet(id, name, values, color, common_persons)


class PersonSetCollection(NamedTuple):
    """The collection of all possible person sets in a given source."""

    id: str
    name: str
    person_sets: Dict[str, PersonSet]
    families: FamiliesData

    @staticmethod
    def _produce_sets(config: NamedTuple) -> Dict[str, PersonSet]:
        """Initializes a dictionary of person set IDs
        mapped to empty PersonSet instances from a given configuration.
        """
        person_set_configs = [*config.domain]
        if config.default is not None:
            person_set_configs.append(config.default)

        return {
            person_set.id: PersonSet(
                person_set.id,
                person_set.name,
                person_set.value,
                person_set.color,
                dict(),
            )
            for person_set in person_set_configs
        }

    @staticmethod
    def get_person_color(
            person: Person, person_set_collection: "PersonSetCollection"):

        if person.generated:
            return "#E0E0E0"

        if person_set_collection is None:
            return "#FFFFFF"

        for person_set in person_set_collection.person_sets.values():
            if person.person_id in person_set.persons:
                return person_set.color

        assert False, (
            f"Person '{person.person_id}' could not be found in any"
            f" domain of '{person_set_collection.id}'!"
        )

    @staticmethod
    def from_families(
            collection_config: NamedTuple,
            families_data: FamiliesData) -> "PersonSetCollection":
        """Produce a PersonSetCollection from its given configuration
        with a pedigree as its source.
        """
        person_set_collection = PersonSetCollection(
            collection_config.id,
            collection_config.name,
            PersonSetCollection._produce_sets(collection_config),
            families_data,
        )
        value_to_id = {
            person_set.value: person_set.id
            for person_set in collection_config.domain
        }
        if collection_config.default is not None:
            value_to_id[
                collection_config.default.value
            ] = collection_config.default.id

        for person_id, person in families_data.persons.items():
            value = person.get_attr(collection_config.source.pedigree.column)

            assert value is not None, (
                f"Missing domain value for"
                f" '{collection_config.source.pedigree.column}'"
                f" in person '{person_id}'!"
            )

            # Convert to string since some of the person's
            # attributes can be of an enum type
            value = str(value)

            if value not in value_to_id:
                if collection_config.default is not None:
                    value = collection_config.default.value
                else:
                    assert value in value_to_id, (
                        f"Domain for '{collection_config.id}'"
                        f" does not have the value '{value}'!"
                    )

            set_id = value_to_id[value]
            person_set_collection.person_sets[set_id].persons[
                person_id
            ] = person

        return person_set_collection

    @staticmethod
    def compose(*person_set_collections, id=None, name="composite collection"):
        if id is None:
            id = ".".join(
                [collection.id for collection in person_set_collections]
            )

        def merge_families(f1, f2):
            families = dict(f1)
            families.update(f2)
            return families

        merged_families = reduce(
            merge_families,
            [collection.families for collection in person_set_collections],
        )

        person_sets_product = product(
            *[
                list(collection.person_sets.values())
                for collection in person_set_collections
            ]
        )

        composed_person_sets = dict()
        for set_combination in person_sets_product:
            set_name = ".".join([ps.value for ps in set_combination])
            composed_set = CompositePersonSet.compose(
                *set_combination, name=set_name
            )
            composed_person_sets[composed_set.id] = composed_set

        return PersonSetCollection(
            id, name, composed_person_sets, merged_families
        )
