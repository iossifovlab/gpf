
from dae.variants.attributes import Sex
from dae.common_reports.people_filters import PeopleGroupFilter


class PeopleCounter(object):

    def __init__(self, families, people_filter):
        self.families = families
        self.people_filter = people_filter

        matched_people = list(self.people_filter.filter(
            self.families.persons.values()))

        self.people_male = len(
            list(PeopleGroupFilter.sex_filter(
                Sex.male).filter(matched_people)))
        self.people_female = len(
            list(PeopleGroupFilter.sex_filter(
                Sex.female).filter(matched_people)))
        self.people_unspecified = len(
            list(PeopleGroupFilter.sex_filter(
                Sex.unspecified).filter(matched_people)))
        self.people_total = len(matched_people)

        assert self.people_total == \
            self.people_male + self.people_female + self.people_unspecified

        self.filter_name = people_filter.filter_name

    def to_dict(self, rows):
        people_counter_dict =\
            {row: getattr(self, row) for row in rows}
        people_counter_dict['column'] = self.filter_name
        return people_counter_dict

    def is_empty(self):
        return self.people_total == 0

    def is_empty_field(self, field):
        assert field in {
            'people_male', 'people_female', 
            'people_unspecified', 'people_total'}
        return getattr(self, field) == 0


class PeopleCounters(object):

    def __init__(self, families, filter_collection):
        self.families = families
        self.filter_collection = filter_collection

        self.counters = self._build_counters()

        self.group_name = filter_collection.name
        self.rows = self._get_row_names()
        self.filter_names = [
            people_counter.filter_name for people_counter in self.counters]

    def to_dict(self):
        return {
            'group_name': self.group_name,
            'columns': self.filter_names,
            'rows': self.rows,
            'counters': [c.to_dict(self.rows) for c in self.counters]
        }

    def _build_counters(self):
        people_counters = [
            PeopleCounter(self.families, filters)
            for filters in self.filter_collection.filters]

        return list(filter(
            lambda people_counter: not people_counter.is_empty(),
            people_counters))

    def _get_column_names(self):
        return []

    def _is_row_empty(self, row):
        return all([
            people_counter.is_empty_field(row)
            for people_counter in self.counters
        ])

    def _get_row_names(self):
        rows = ['people_male', 'people_female',
                'people_unspecified', 'people_total']
        return [row for row in rows
                if not self._is_row_empty(row)]
