from typing import List, Dict, NamedTuple

from dae.pedigrees.family import Person, FamiliesData


class PersonSet(NamedTuple):
    id: str
    name: str
    color: str
    source: str
    value: str
    persons: List[Person]


class PersonSetCollection(NamedTuple):
    id: str
    name: str
    person_sets: Dict[str, PersonSet]
    families: FamiliesData
