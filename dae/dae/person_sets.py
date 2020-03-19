"""This module provides functionality for grouping
individuals from a study or study group into various
sets based on what value they have in a given mapping.
"""

from typing import Dict, NamedTuple

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
    def _produce_sets(config: NamedTuple) -> Dict[str, PersonSet]:
        """Initializes a dictionary of person set IDs
        mapped to empty PersonSet instances from a given configuration.
        """
        return {
            person_set.id: PersonSet(*person_set, dict())
            for person_set in config.domain
        }

    @staticmethod
    def get_person_color(
        person: Person, person_set_collection: "PersonSetCollection"
    ):
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
        collection_config: NamedTuple, families_data: FamiliesData
    ) -> "PersonSetCollection":
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

            assert value in value_to_id, (
                f"Domain for '{collection_config.id}'"
                f" does not have the value '{value}'!"
            )

            set_id = value_to_id[value]
            person_set_collection.person_sets[set_id].persons[
                person_id
            ] = person

        return person_set_collection
