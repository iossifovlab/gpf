import itertools
from collections import namedtuple
from collections.abc import Mapping
from functools import lru_cache

from box import Box

from dae.variants.attributes import Role
from dae.pedigrees.family import FamiliesData


class PeopleGroup:

    ValueDescriptor = namedtuple("ValueDescriptor", [
        'id', 'name', 'color', 'index'
    ])

    def __init__(
            self, people_group_id, name=None, domain=None, default=None,
            source=None, getter=None):
        self.id = people_group_id
        self.name = name
        self._domain = domain
        self._default = default
        self._source = source
        self._legend = None

        if getter is not None:
            self._getter = getter
        else:
            self._getter = lambda person: person.get_attr(self.source)

    @property
    def domain(self):
        return self._domain

    @property
    def default(self):
        return self._default

    @property
    def source(self):
        return self._source

    @property
    def getter(self):
        return self._getter

    @staticmethod
    def grayscale32(index):
        val = 255 - 8 * (index % 32)
        res = f'#{val:x}{val:x}{val:x}'
        return res

    @staticmethod
    def from_config(people_group_id, people_group_config, getter=None):
        return PeopleGroup(
            people_group_id,
            name=people_group_config.name,
            domain={
                value['id']: PeopleGroup.ValueDescriptor(index=index, **value)
                for index, value in enumerate(
                    people_group_config.domain.values())
            },
            default=PeopleGroup.ValueDescriptor(
                **people_group_config.default,
                index=999_999_999),
            source=people_group_config.source,
            getter=getter
        )

    missing_person = ValueDescriptor(
            id='missing-person',
            name='missing-person',
            color='#E0E0E0',
            index=1_000_000_000,
        )

    def person_color(self, person):
        if person.generated:
            return self.missing_person.color
        propvalue = self.getter(person)
        return self.domain.get(propvalue, self.default).color

    @property
    def legend(self):
        if self._legend is None:
            result = list(self.domain.values())
            result.append(self.default)
            result.append(self.missing_person)
            self._legend = [
                {
                    "id": dv.id,
                    "name": dv.name,
                    "color": dv.color
                }
                for dv in result
            ]
        return self._legend

    def family_pedigree(self, family):
        result = [
            [
                p.family_id,
                p.person_id,
                p.mom_id if p.mom_id else '0',
                p.dad_id if p.dad_id else '0',
                p.sex.short(),
                str(p.role),
                self.person_color(p),
                p.layout,
                p.generated,
                '',
                ''
            ]
            for p in family.persons.values()]
        return result


class PeopleMultiGroup(PeopleGroup):

    def __init__(
            self, people_groups):
        super(PeopleMultiGroup, self).__init__(
            ".".join([pg.id for pg in people_groups]),
            name=" and ".join([pg.name for pg in people_groups]),
            domain=None,
            default=None,
            source=None,
            getter=None)
        self.people_groups = people_groups

    @property
    def domain(self):
        if self._domain is None:
            domain = {
                str(tuple([dv.id for dv in value])):
                    PeopleGroup.ValueDescriptor(index=index, **{
                        'id': str(tuple([dv.id for dv in value])),
                        'name': tuple([dv.name for dv in value]),
                        'color': value[0].color
                    })
                for index, value in enumerate(itertools.product(*[
                    pg.domain.values()
                    for pg in self.people_groups]))
            }
            self._domain = domain
        return self._domain

    @property
    def default(self):
        if self._default is None:
            defaults = [pg.default for pg in self.people_groups]

            self._default = PeopleGroup.ValueDescriptor(
                index=999_999_999,
                id=str(tuple([dv.id for dv in defaults])),
                name=tuple([dv.name for dv in defaults]),
                color=defaults[0].color
            )
        return self._default

    @property
    def getter(self):
        return lambda person: str(tuple(
            [pg.getter(person) for pg in self.people_groups]
        ))


PEOPLE_GROUP_ROLES = PeopleGroup.from_config(
    'role',
    Box({
        'name': 'Role',
        'domain': {
            str(r): {
                'id': str(r),
                'name': str(r),
                'color': PeopleGroup.grayscale32(index)
            } for index, r in enumerate(Role.__members__)
        },
        'default': {
            'id': 'unknown',
            'name': 'unknown',
            'color': '#bbbbbb'
        },
        'source': 'role'
    })
)


PEOPLE_GROUP_FAMILY_SIZES = PeopleGroup.from_config(
    'family_size',
    Box({
        'name': 'Family Size',
        'domain': {
            str(size): {
                'id': str(size),
                'name': str(size),
                'color': PeopleGroup.grayscale32(size)
            } for size in range(32, 1, -1)
        },
        'default': {
            'id': '>=32',
            'name': '>=32',
            'color': '#bbbbbb'
        },
        'source': 'size'
    }),
    getter=lambda person: str(len(person.family))
)


PEOPLE_GROUP_SEXES = PeopleGroup.from_config(
    'sex',
    Box({
        'name': 'Sex',
        'domain': {
            'M': {
                'id': 'M',
                'name': 'M',
                'color': '#e35252',
            },
            'F': {
                'id': 'F',
                'name': 'F',
                'color': '#b8008a',
            },
            'U': {
                'id': 'U',
                'name': 'U',
                'color': '#aaaaaa',
            }
        },
        'default': {
            'id': 'U',
            'name': 'U',
            'color': '#aaaaaa',
        },
        'source': 'sex',
    }, default_box=True))


PEOPLE_GROUP_ROLES_SEXES = PeopleMultiGroup([
    PEOPLE_GROUP_ROLES,
    PEOPLE_GROUP_SEXES
])


PEOPLE_GROUP_STATUS = PeopleGroup.from_config(
    'status',
    Box({
        'name': 'Status',
        'domain': {
            'affected': {
                'id': 'affected',
                'name': 'affected',
                'color': '#e35252',
            },
            'unaffected': {
                'id': 'unaffected',
                'name': 'unaffected',
                'color': '#b8008a',
            },
            'unspecified': {
                'id': 'unspecified',
                'name': 'unspecified',
                'color': '#aaaaaa',
            }
        },
        'default': {
            'id': 'unknown',
            'name': 'unknown',
            'color': '#bbbbbb',
        },
        'source': 'status',
    }, default_box=True))


class FamiliesGroup(PeopleGroup):
    def __init__(self, families, people_group):
        super(FamiliesGroup, self).__init__(
            people_group.id,
            name=people_group.name,
            domain=people_group.domain,
            default=people_group.default,
            source=people_group.source,
            getter=people_group.getter)

        assert isinstance(families, FamiliesData)

        self.families = families
        self.people_group = people_group
        self._available_values = None
        self._families_types = None
        self._available_families_types = None

    @property
    def available_values(self):
        if self._available_values is None:
            values = set([
                self.getter(p)
                for p in self.families.persons.values()
            ])
            values = set([
                self.domain.get(str(v), self.default).id
                for v in values
            ])
            self._available_values = sorted(
                list(values),
                key=lambda dv: self.domain.get(dv, self.default).index)
        return self._available_values

    def calc_family_type(self, family):
        values = [
            self.getter(p)
            for p in family.members_in_order
        ]
        values = [
            self.domain.get(str(v), self.default).id
            for v in values
        ]
        values = sorted(
            values,
            key=lambda dv: self.domain.get(dv, self.default).index)
        result = tuple(values)
        return result

    @property
    def families_types(self):
        if self._families_types is None:
            self._families_types = [
                self.calc_family_type(family)
                for family in self.families.values()
            ]
        return self._families_types

    @property
    def available_families_types(self):
        if self._available_families_types is None:
            families_types = set(self.families_types)

            def ft_key(ft):
                return tuple(
                    map(
                        lambda dv: self.domain.get(
                            dv, self.default).index,
                        ft
                    )
                )

            self._available_families_types = sorted(
                list(families_types), key=ft_key)
        return self._available_families_types

    @lru_cache(maxsize=32)
    def get_people_with_propvalues(self, propvalues):
        propvalues = set([
            self.domain.get(str(dv), self.default).id for dv in propvalues
        ])
        return list(filter(
            lambda p: not p.generated and self.getter(p) in propvalues,
            self.families.persons.values()))


class FamiliesSizeGroup(FamiliesGroup):
    def __init__(self, families):
        super(FamiliesSizeGroup, self).__init__(
            families,
            PEOPLE_GROUP_FAMILY_SIZES
        )

    def calc_family_type(self, family):
        result = (str(len(family)),)
        return result


class FamiliesGroups(Mapping):

    def __init__(self, families):
        assert isinstance(families, FamiliesData)
        self.families = families
        self._families_groups = {}

    def __getitem__(self, family_id):
        return self._families_groups[family_id]

    def __len__(self):
        return len(self._families_groups)

    def __iter__(self):
        return iter(self._families_groups)

    def __contains__(self, family_id):
        return family_id in self._families_groups

    def keys(self):
        return self._families_groups.keys()

    def values(self):
        return self._families_groups.values()

    def items(self):
        return self._families_groups.items()

    def get(self, family_id, default=None):
        return self._families_groups.get(family_id, default)

    def has_families_group(self, people_group_id):
        return people_group_id in self._families_groups

    def get_families_group(self, people_group_id):
        return self._families_groups.get(people_group_id)

    def get_default_families_group(self):
        return next(iter(self._families_groups.values()))

    def add_families_group(self, people_group):
        if people_group.id in self._families_groups:
            print(
                f"WARN: adding {people_group.id} more than once! "
                "Skipping...")
            return
        families_group = FamiliesGroup(self.families, people_group)
        self._families_groups[families_group.id] = families_group

    def add_predefined_groups(self, attributes):
        # assert attribute in {'role', 'status', 'sex'}, attribute
        for attribute in attributes:
            if attribute == 'role':
                self.add_families_group(PEOPLE_GROUP_ROLES)
            elif attribute == 'sex':
                self.add_families_group(PEOPLE_GROUP_SEXES)
            elif attribute == 'role.sex':
                self.add_families_group(PEOPLE_GROUP_ROLES_SEXES)
            elif attribute == 'status':
                self.add_families_group(PEOPLE_GROUP_STATUS)
            elif attribute == 'family_size':
                self._families_groups['family_size'] = FamiliesSizeGroup(
                    self.families
                )
            else:
                raise ValueError(
                    f"unexpected predefined people group attribute: "
                    "{attribute}; supported predefined attributes are "
                    "'role', 'sex', 'status")

    @staticmethod
    def from_config(families, people_groups_config):
        result = FamiliesGroups(families)

        for people_group_id in people_groups_config:
            people_group = PeopleGroup.from_config(
                people_group_id,
                people_groups_config[people_group_id]
            )
            result.add_families_group(people_group)
        return result
