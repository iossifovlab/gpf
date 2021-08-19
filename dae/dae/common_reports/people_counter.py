from collections import OrderedDict

from dae.variants.attributes import Sex


class PeopleCounter(object):
    def __init__(self, families, person_set):
        self.families = families
        self.person_set = person_set

        matched_people = list(self.person_set.persons.values())

        self.people_male = len(
            list(filter(lambda p: p.sex == Sex.male, matched_people))
        )
        self.people_female = len(
            list(filter(lambda p: p.sex == Sex.female, matched_people))
        )
        self.people_unspecified = len(
            list(filter(lambda p: p.sex == Sex.unspecified, matched_people))
        )
        self.people_total = len(matched_people)

        assert (
            self.people_total
            == self.people_male + self.people_female + self.people_unspecified
        )

    def to_dict(self, rows):
        people_counter_dict = {row: getattr(self, row) for row in rows}
        people_counter_dict["column"] = self.person_set.name
        return people_counter_dict

    def is_empty(self):
        return self.people_total == 0

    def is_empty_field(self, field):
        assert field in {
            "people_male",
            "people_female",
            "people_unspecified",
            "people_total",
        }
        return getattr(self, field) == 0


class PeopleCounters(object):
    def __init__(self, families, person_set_collection):
        self.families = families
        self.person_set_collection = person_set_collection

        self.counters = self._build_counters()

        self.group_name = person_set_collection.name
        self.rows = self._get_row_names()
        self.column_names = [
            people_counter.person_set.name for people_counter in self.counters
        ]

    def to_dict(self):
        return {
            "group_name": self.group_name,
            "columns": self.column_names,
            "rows": self.rows,
            "counters": [c.to_dict(self.rows) for c in self.counters],
        }

    def _build_counters(self):
        people_counters = [
            PeopleCounter(self.families, person_set)
            for person_set in self.person_set_collection.person_sets.values()
        ]

        return list(
            filter(
                lambda people_counter: not people_counter.is_empty(),
                people_counters,
            )
        )

    def _get_column_names(self):
        return []

    def _is_row_empty(self, row):
        return all(
            [
                people_counter.is_empty_field(row)
                for people_counter in self.counters
            ]
        )

    def _get_row_names(self):
        rows = [
            "people_male",
            "people_female",
            "people_unspecified",
            "people_total",
        ]
        return [row for row in rows if not self._is_row_empty(row)]


class PeopleReport:
    def __init__(self, families, person_set_collections):
        self.families = families
        self.person_set_collections = person_set_collections

        self.people_counters_collection = \
            self._create_people_counters_collection()

    def _create_people_counters_collection(self):
        return [
            PeopleCounters(self.families, person_set_collection)
            for person_set_collection in self.person_set_collections
        ]

    def to_dict(self):
        return OrderedDict(
            [
                (
                    "people_counters",
                    [pc.to_dict() for pc in self.people_counters_collection],
                ),
            ]
        )
