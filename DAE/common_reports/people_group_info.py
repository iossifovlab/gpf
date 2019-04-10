from __future__ import unicode_literals
from __future__ import division

from collections import OrderedDict


class PeopleGroupInfo(object):

    def __init__(
            self, people_group_info, people_group, study=None,
            people_groups=[]):
        self.name = people_group_info['name']
        self.domain = people_group_info['values']
        self.default = people_group_info['default']
        self.source = people_group_info['source']

        self.people_groups = self._get_people_groups(study)\
            if study is not None and len(people_groups) == 0 else people_groups

        self.people_group = people_group

    def _get_people_groups(self, study):
        return list([
            str(p) for p in study.get_pedigree_values(self.source)])

    def _is_default(self, people_group):
        return people_group not in self.domain.keys()

    def get_people_groups(self):
        return list(frozenset([
            people_group
            if not self._is_default(people_group) else self.default['name']
            for people_group in self.people_groups
        ]))

    @property
    def missing_person_info(self):
        return OrderedDict([
            ('id', 'missing-person'),
            ('name', 'missing-person'),
            ('color', '#E0E0E0')
        ])


class PeopleGroupsInfo(object):

    def __init__(self, study, filter_info, people_groups_info):
        self.study = study
        self.filter_info = filter_info
        self.people_groups_info = people_groups_info

        self.people_groups_info = self._get_people_groups_info()

    def _get_people_groups_info(self):
        return [
            PeopleGroupInfo(
                self.people_groups_info[people_group], people_group,
                study=self.study)
            for people_group in self.filter_info['people_groups']
        ]

    def get_first_people_group_info(self):
        return self.people_groups_info[0]

    def has_people_group_info(self, people_group):
        return len(list(filter(
            lambda people_group_info:
            people_group_info.people_group == people_group,
            self.people_groups_info))) != 0

    def get_people_group_info(self, people_group):
        people_groups_info = list(filter(
            lambda people_group_info:
            people_group_info.people_group == people_group,
            self.people_groups_info))
        return people_groups_info[0] if len(people_groups_info) != 0 else []
