"""This module provides functionality for grouping
individuals from a study or study group into various
sets based on what value they have in a given mapping.
"""

from typing import Dict, NamedTuple
from dae.configuration.gpf_config_parser import FrozenBox
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


class PersonSetCollection(NamedTuple):
    """The collection of all possible person sets in a given source."""

    id: str
    name: str
    person_sets: Dict[str, PersonSet]
    families: FamiliesData

    @staticmethod
    def _produce_sets(config: FrozenBox) -> Dict[str, PersonSet]:
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

        print(
            f"Person '{person.person_id}' could not be found in any"
            f" domain of '{person_set_collection.id}'!"
        )
        return "#AAAAAA"

    @staticmethod
    def remove_empty_person_sets(person_set_collection):
        empty_person_sets = set()
        for set_id, person_set in person_set_collection.person_sets.items():
            if len(person_set.persons) == 0:
                empty_person_sets.add(set_id)
        for set_id in empty_person_sets:
            del person_set_collection.person_sets[set_id]
        return person_set_collection

    @staticmethod
    def from_families(
            collection_config: FrozenBox,
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

            # Convert to string since some of the person's
            # attributes can be of an enum type
            if value is not None:
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

        return PersonSetCollection.remove_empty_person_sets(
            person_set_collection)

    @staticmethod
    def merge(person_set_collections, families, id, name):

        new_collection = PersonSetCollection(
            id, name, dict(), families,
        )

        all_person_sets = list()

        for collection in person_set_collections:
            assert collection.id == new_collection.id
            all_person_sets.extend(collection.person_sets.items())

        all_person_sets = sorted(all_person_sets, key=lambda i: i[0])

        for person_set_id, person_set in all_person_sets:
            if person_set_id not in new_collection.person_sets:
                new_collection.person_sets[person_set_id] = PersonSet(
                    person_set.id,
                    person_set.name,
                    person_set.value,
                    person_set.color,
                    dict(),
                )
            for person_id, person in person_set.persons.items():
                if person_id in families.persons:
                    new_collection.person_sets[person_set_id].persons[
                        person_id
                    ] = person

        return new_collection
