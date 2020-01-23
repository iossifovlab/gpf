import itertools
from dae.variants.attributes import Sex
from dae.pedigrees.families_groups import PeopleGroup, \
    PEOPLE_GROUP_SEXES


class PeopleFilter:

    @property
    def id(self):
        raise NotImplementedError()

    @property
    def group_id(self):
        return self.people_group.id

    @property
    def title(self):
        raise NotImplementedError()

    @property
    def filter_name(self):
        raise NotImplementedError()

    def match(self, person):
        raise NotImplementedError()

    def filter(self, persons):
        return filter(lambda p: not p.generated and self.match(p), persons)


class PeopleGroupFilter(PeopleFilter):

    def __init__(self, people_group, specified_value, name):
        assert isinstance(people_group, PeopleGroup)

        self.people_group = people_group
        self.specified_value = str(specified_value)
        self._name = name
        self.people_with_parents_and_filter_ids = None

    @property
    def title(self):
        return self.people_group.name

    @property
    def group_id(self):
        return self.people_group.id

    @property
    def id(self):
        return f"{self.people_group.id}.{self.specified_value}"

    @property
    def filter_name(self):
        return self._name

    def match(self, person):
        return self.people_group.getter(person) == self.specified_value

    @staticmethod
    def sex_filter(sex):
        assert isinstance(sex, Sex)
        if sex == Sex.M:
            return PeopleGroupFilter(PEOPLE_GROUP_SEXES, Sex.M, 'Male')
        elif sex == Sex.F:
            return PeopleGroupFilter(PEOPLE_GROUP_SEXES, Sex.F, 'Female')
        elif sex == Sex.U:
            return PeopleGroupFilter(PEOPLE_GROUP_SEXES, Sex.U, 'Unspecified')
        else:
            raise ValueError(f'unexpeced sex: {sex}')


class MultiFilter(PeopleFilter):

    def __init__(self, filters=[]):
        assert all([isinstance(f, PeopleFilter) for f in filters])
        self._filters = filters
        self.people_with_parents_and_filter_ids = None

    @property
    def group_id(self):
        return '&'.join(set([f.group_id for f in self._filters]))

    @property
    def id(self):
        return ';'.join([f.id for f in self._filters])

    def add_filter(self, filt):
        assert isinstance(filt, PeopleFilter)
        self._filters.append(filt)

    @property
    def title(self):
        return ' and '.join([
            filt.people_group.name for filt in self._filters
        ])

    @property
    def filter_name(self):
        return ' and '.join(
            [filt.filter_name for filt in self._filters])

    @staticmethod
    def from_list(filters):
        return [MultiFilter(list(filt)) for filt in filters]

    def match(self, person):
        return all([filt.match(person) for filt in self._filters])


class FilterCollection(object):

    def __init__(self, name, filters=[]):
        self.name = name
        assert all([isinstance(fo, PeopleFilter) for fo in filters])
        self._filters = filters

    @property
    def group_id(self):
        return '&'.join(set([f.group_id for f in self._filters]))

    @property
    def id(self):
        return '#'.join([f.id for f in self._filters])

    @property
    def filters(self):
        return self._filters

    def add_filter(self, filt):
        assert isinstance(filt, PeopleFilter)
        self._filters.append(filt)

    def get_filter_names(self):
        assert all(
            [isinstance(fo, PeopleFilter) for fo in self._filters])

        return [filt.filter_name for filt in self._filters]

    def get_filter_by_name(self, name):
        for filt in self.filters:
            if filt.filter_name == name:
                return filt
        return None

    @staticmethod
    def build_filter_objects(families_groups, groups):
        filter_objects = []
        for name, people_group_ids in groups.items():
            filters = []
            for people_group_id in people_group_ids:
                assert people_group_id in families_groups, \
                    f'{people_group_id} not in {families_groups.keys()}'
                families_group = \
                    families_groups.get(people_group_id)

                filt = []
                for group_value in families_group.available_values:
                    filt.append(PeopleGroupFilter(
                        families_group, group_value, name=group_value))
                filters.append(filt)

            filter_objects.append(FilterCollection(
                name,
                MultiFilter.from_list(
                    list(itertools.product(*filters)))))

        return filter_objects
