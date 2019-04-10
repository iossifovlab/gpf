from __future__ import unicode_literals
from __future__ import division

from collections import OrderedDict

from variants.attributes import Sex


class PeopleCounter(object):

    def __init__(self, families, filter_object):
        self.families = families
        self.filter_object = filter_object

        self.people_male = len(self._get_people(Sex.male))
        self.people_female = len(self._get_people(Sex.female))
        self.people_unspecified = len(self._get_people(Sex.unspecified))
        self.people_total =\
            self.people_male + self.people_female + self.people_unspecified

        self.column = filter_object.get_column_name()

    def to_dict(self, rows):
        people_counter_dict =\
            OrderedDict([(row, getattr(self, row)) for row in rows])
        people_counter_dict['column'] = self.column
        return people_counter_dict

    def _get_people(self, sex):
        people = []

        for family in self.families.values():
            people += list(filter(
                lambda pwr: pwr.sex == sex and
                all([pwr.get_attr(filt.column) == filt.value
                     for filt in self.filter_object.filters]),
                family.members_in_order))

        return people

    def is_empty(self):
        return self.people_total == 0

    def is_empty_field(self, field):
        return getattr(self, field) == 0


class PeopleCounters(object):

    def __init__(self, families, filter_object):
        self.families = families
        self.filter_object = filter_object

        self.counters = self._get_counters()

        self.group_name = filter_object.name
        self.rows = self._get_row_names()
        self.columns = self._get_column_names()

    def to_dict(self):
        return OrderedDict([
            ('group_name', self.group_name),
            ('columns', self.columns),
            ('rows', self.rows),
            ('counters', [c.to_dict(self.rows) for c in self.counters])
        ])

    def _get_counters(self):
        people_counters = [PeopleCounter(self.families, filters)
                           for filters in self.filter_object.filter_objects]

        return list(filter(
            lambda people_counter: not people_counter.is_empty(),
            people_counters))

    def _get_column_names(self):
        return [people_counter.column for people_counter in self.counters]

    def _is_row_empty(self, row):
        return all([people_counter.is_empty_field(row)
                    for people_counter in self.counters])

    def _get_row_names(self):
        rows = ['people_male', 'people_female',
                'people_unspecified', 'people_total']
        return [row for row in rows
                if not self._is_row_empty(row)]
