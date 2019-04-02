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

    def get_column(self):
        return str(self.column_value)


class FilterObject(object):

    def __init__(self, filters=[]):
        self.filters = filters

    def add_filter(self, column, value):
        self.filters.append(Filter(column, value))

    def get_column(self):
        return ' and '.join([filter.get_column() for filter in self.filters])

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
        return [filter_object.get_column()
                for filter_object in self.filter_objects]

    @staticmethod
    def get_filter_objects(query_object, phenotypes_info, groups):
        filter_objects = []
        for name, group in groups.items():
            filters = []
            for el in group:
                if phenotypes_info.has_phenotype_info(el):
                    phenotype_info = phenotypes_info.get_phenotype_info(el)
                    el_column = phenotype_info.source
                    el_values = phenotype_info.phenotypes
                else:
                    el_column = el
                    el_values = query_object.get_pedigree_values(el)

                filter = []
                for el_value in el_values:
                    if phenotypes_info.has_phenotype_info(el) and\
                            el_value is None:
                        phenotype_info = phenotypes_info.get_phenotype_info(el)
                        filter.append(Filter(el_column, el_value,
                                             phenotype_info.default['name']))
                    else:
                        filter.append(Filter(el_column, el_value))
                filters.append(filter)

            filter_objects.append(FilterObjects(name, FilterObject.from_list(
                list(itertools.product(*filters)))))

        return filter_objects
