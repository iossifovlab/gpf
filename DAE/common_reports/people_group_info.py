from __future__ import unicode_literals
from __future__ import division

from collections import OrderedDict


class PeopleGroupInfo(object):

    def __init__(
            self, people_group_info, phenotype_group, study=None,
            phenotypes=None):
        self.name = people_group_info['name']
        self.domain = people_group_info['domain']
        self.unaffected = people_group_info['unaffected']
        self.default = people_group_info['default']
        self.source = people_group_info['source']

        self.phenotypes = self._get_phenotypes(study)\
            if phenotypes is None else phenotypes

        self.phenotype_group = phenotype_group

    def _get_phenotypes(self, study):
        return list([
            str(p) for p in study.get_pedigree_values(self.source)])

    def get_phenotypes(self):
        return [
            phenotype if phenotype is not None else self.default['name']
            for phenotype in self.phenotypes
        ]

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
                self.people_groups_info[phenotype_group], phenotype_group,
                study=self.study)
            for phenotype_group in self.filter_info['phenotype_groups']
        ]

    def get_first_people_group_info(self):
        return self.people_groups_info[0]

    def has_people_group_info(self, phenotype_group):
        return len(list(filter(
            lambda people_group_info:
            people_group_info.phenotype_group == phenotype_group,
            self.people_groups_info))) != 0

    def get_people_group_info(self, phenotype_group):
        return list(filter(
            lambda people_group_info:
            people_group_info.phenotype_group == phenotype_group,
            self.people_groups_info))[0]
