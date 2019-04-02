from __future__ import unicode_literals
from __future__ import division

from collections import OrderedDict


class PhenotypeInfo(object):

    def __init__(
            self, phenotype_info, phenotype_group, query_object=None,
            phenotypes=None):
        self.name = phenotype_info['name']
        self.domain = phenotype_info['domain']
        self.unaffected = phenotype_info['unaffected']
        self.default = phenotype_info['default']
        self.source = phenotype_info['source']

        self.phenotypes = self._get_phenotypes(query_object)\
            if phenotypes is None else phenotypes

        self.phenotype_group = phenotype_group

    def _get_phenotypes(self, query_object):
        return list([
            str(p) for p in query_object.get_pedigree_values(self.source)])

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


class PhenotypesInfo(object):

    def __init__(self, query_object, filter_info, phenotypes_info):
        self.phenotypes_info = self._get_phenotypes_info(
            query_object, filter_info, phenotypes_info)

    def _get_phenotypes_info(
            self, query_object, filter_info, phenotypes_info):
        return [
            PhenotypeInfo(phenotypes_info[phenotype_group], phenotype_group,
                          query_object=query_object)
            for phenotype_group in filter_info['phenotype_groups']
        ]

    def get_first_phenotype_info(self):
        return self.phenotypes_info[0]

    def has_phenotype_info(self, phenotype_group):
        return len(list(filter(
            lambda phenotype_info:
            phenotype_info.phenotype_group == phenotype_group,
            self.phenotypes_info))) != 0

    def get_phenotype_info(self, phenotype_group):
        return list(filter(
            lambda phenotype_info:
            phenotype_info.phenotype_group == phenotype_group,
            self.phenotypes_info))[0]
