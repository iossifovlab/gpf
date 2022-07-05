from dae.variants.attributes import Sex


class PeopleCounter:
    """Class representing a people counter JSON."""

    def __init__(self, json):
        self.person_set_name = json["column"]
        self.people_male = json.get("people_male", 0)
        self.people_female = json.get("people_female", 0)
        self.people_unspecified = json.get("people_unspecified", 0)
        self.people_total = json.get("people_total", 0)

    @staticmethod
    def from_families(families, person_set):
        """Build people counter JSON from dict of families."""
        matched_people = list(person_set.persons.values())

        people_male = len(
            list(filter(lambda p: p.sex == Sex.male, matched_people))
        )
        people_female = len(
            list(filter(lambda p: p.sex == Sex.female, matched_people))
        )
        people_unspecified = len(
            list(filter(lambda p: p.sex == Sex.unspecified, matched_people))
        )
        people_total = len(matched_people)

        assert (
            people_total == people_male + people_female + people_unspecified
        )

        return PeopleCounter({
            "column": person_set.name,
            "people_male": people_male,
            "people_female": people_female,
            "people_unspecified": people_unspecified,
            "people_total": people_total
        })

    def to_dict(self, rows):
        people_counter_dict = {row: getattr(self, row) for row in rows}
        people_counter_dict["column"] = self.person_set_name
        return people_counter_dict

    def is_empty(self):
        return self.people_total == 0

    def is_empty_field(self, field):
        """Return whether a given field has not counted a single variant."""
        assert field in {
            "people_male",
            "people_female",
            "people_unspecified",
            "people_total",
        }
        return getattr(self, field) == 0


class PeopleCounters:
    """Class representing people counters JSON."""

    def __init__(self, json):
        self.group_name = json["group_name"]
        self.columns = json["columns"]
        self.rows = json["rows"]
        self.counters = [PeopleCounter(d) for d in json["counters"]]

    @staticmethod
    def from_families(families, person_set_collection):
        """Create people counters JSON from dict of families."""
        people_counters = [
            PeopleCounter.from_families(families, person_set)
            for person_set in person_set_collection.person_sets.values()
        ]

        people_counters = list(
            filter(
                lambda people_counter: not people_counter.is_empty(),
                people_counters,
            )
        )

        group_name = person_set_collection.name
        rows = [
            "people_male",
            "people_female",
            "people_unspecified",
            "people_total",
        ]

        def is_row_empty(row):
            return all(
                people_counter.is_empty_field(row)
                for people_counter in people_counters
            )

        rows = [row for row in rows if not is_row_empty(row)]

        column_names = [
            pc.person_set_name for pc in people_counters
        ]

        return PeopleCounters({
            "group_name": group_name,
            "columns": column_names,
            "rows": rows,
            "counters": [pc.to_dict(rows) for pc in people_counters]
        })

    def to_dict(self):
        return {
            "group_name": self.group_name,
            "columns": self.columns,
            "rows": self.rows,
            "counters": [c.to_dict(self.rows) for c in self.counters],
        }


class PeopleReport:
    """Class representing people report JSON."""

    def __init__(self, json):
        self.people_counters = [PeopleCounters(d) for d in json]

    @staticmethod
    def from_families(families, person_set_collections):
        people_counters_collection = [
            PeopleCounters.from_families(families, person_set_collection)
            for person_set_collection in person_set_collections
        ]
        return PeopleReport(
            [pc.to_dict() for pc in people_counters_collection]
        )

    def to_dict(self):
        return [pc.to_dict() for pc in self.people_counters]
