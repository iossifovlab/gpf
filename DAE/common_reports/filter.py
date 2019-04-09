from __future__ import unicode_literals
from __future__ import division

import itertools


class Filter(object):

    def __init__(self, column, value, column_value=None):
        value = str(value)
        self.column = column
        self.value = value
        self.column_value =\
            column_value if column_value is not None else value

    def get_column_name(self):
        return str(self.column_value)


class FilterObject(object):

    def __init__(self, filters=[]):
        self.filters = filters

    def add_filter(self, column, value, column_value=None):
        self.filters.append(Filter(column, value, column_value))

    def get_column_name(self):
        return ' and '.join(
            [filter.get_column_name() for filter in self.filters])

    @staticmethod
    def from_list(filters):
        return [FilterObject(list(filter)) for filter in filters]


class FilterObjects(object):

    def __init__(self, name, filter_objects=[]):
        self.name = name
        self.filter_objects = filter_objects

    def add_filter_object(self, filter_object):
        self.filter_objects.append(filter_object)

    def get_columns(self):
        return [filter_object.get_column_name()
                for filter_object in self.filter_objects]

    @staticmethod
    def get_filter_objects(study, people_groups_info, groups):
        filter_objects = []
        for name, group in groups.items():
            filters = []
            for el in group:
                if people_groups_info.has_people_group_info(el):
                    people_group_info = \
                        people_groups_info.get_people_group_info(el)
                    el_column = people_group_info.source
                    el_values = people_group_info.people_groups
                else:
                    el_column = el
                    el_values = study.get_pedigree_values(el)

                filter = []
                for el_value in el_values:
                    if people_groups_info.has_people_group_info(el):
                        people_group_info = \
                            people_groups_info.get_people_group_info(el)
                        if people_group_info._is_default(el_value):
                            filter.append(Filter(
                                el_column, el_value,
                                people_group_info.default['name']))
                            continue
                    filter.append(Filter(el_column, el_value))
                filters.append(filter)

            filter_objects.append(FilterObjects(name, FilterObject.from_list(
                list(itertools.product(*filters)))))

        return filter_objects
