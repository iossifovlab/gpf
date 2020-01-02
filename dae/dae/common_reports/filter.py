import itertools
from dae.pedigrees.family import FamiliesGroup


class Filter(object):

    def __init__(self, families_group, specified_value, name):
        assert isinstance(families_group, FamiliesGroup)

        self.families_group = families_group
        self.specified_value = str(specified_value)
        self.name = name

    def eval(self, person):
        return self.families_group.getter(person) == self.specified_value


class FilterObject(object):

    def __init__(self, filters=[]):
        assert all([isinstance(f, Filter) for f in filters])
        self._filters = filters

    def add_filter(self, filt):
        assert isinstance(filt, Filter)
        self._filters.append(filt)

    # def add_filter(self, column, value, column_value=None):
    #     self.filters.append(Filter(column, value, column_value))

    @property
    def name(self):
        return ' and '.join([
            filt.families_group.name for filt in self._filters
        ])

    @property
    def filters(self):
        return self._filters

    def get_column_name(self):
        return ' and '.join(
            [filt.name for filt in self._filters])

    @staticmethod
    def from_list(filters):
        return [FilterObject(list(filt)) for filt in filters]


class FilterObjects(object):

    def __init__(self, filter_objects=[]):
        assert all([isinstance(fo, FilterObject) for fo in filter_objects])
        self._filter_objects = filter_objects

    @property
    def name(self):
        print([fo.name for fo in self._filter_objects])
        return self._filter_objects[0].name

    @property
    def filter_objects(self):
        return self._filter_objects

    def add_filter_object(self, filter_object):
        assert isinstance(filter_object, FilterObject)
        self._filter_objects.append(filter_object)

    def get_columns(self):
        assert all(
            [isinstance(fo, FilterObject) for fo in self._filter_objects])

        return [
            filter_object.get_column_name()
            for filter_object in self._filter_objects]

    def get_filter_object_by_column_name(self, name):
        for fo in self.filter_objects:
            print(fo.get_column_name())
            if fo.get_column_name() == name:
                return fo
        return None

    @staticmethod
    def build_filter_objects(families_groups, groups):
        print(groups)
        filter_objects = []
        for name, people_group_ids in groups.items():
            filters = []
            for people_group_id in people_group_ids:
                assert families_groups.has_families_group(people_group_id), \
                    f'{people_group_id} not in {families_groups.keys()}'
                families_group = \
                    families_groups.get_families_group(people_group_id)

                filt = []
                for group_value in families_group.available_values:
                    filt.append(Filter(
                        families_group, group_value, name=group_value))
                filters.append(filt)

            filter_objects.append(FilterObjects(
                FilterObject.from_list(
                    list(itertools.product(*filters)))))

        return filter_objects
