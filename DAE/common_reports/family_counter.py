from __future__ import unicode_literals
from __future__ import division

import pandas as pd
from collections import defaultdict, OrderedDict


class FamilyCounter(object):

    def __init__(self, family, counter, phenotype_info):
        self.pedigree = self._get_pedigree(family, phenotype_info)
        self.pedigrees_count = counter

    def to_dict(self):
        return OrderedDict([
            ('pedigree', self.pedigree),
            ('pedigrees_count', self.pedigrees_count)
        ])

    def _get_member_color(self, member, phenotype_info):
        if member.generated:
            return '#E0E0E0'
        else:
            pheno = member.get_attr(phenotype_info.source)
            domain = phenotype_info.domain.get(pheno, None)
            if domain and pheno:
                return domain['color']
            else:
                return phenotype_info.default['color']

    def _get_pedigree(self, family, phenotype_info):
        return [[member.family_id, member.person_id, member.dad_id,
                 member.mom_id, member.sex.short(), str(member.role),
                 self._get_member_color(member, phenotype_info),
                 member.layout_position, member.generated, '', '']
                for member in family.members_in_order]


class FamiliesCounter(object):

    def __init__(
            self, families, phenotype_info, draw_all_families,
            families_count_show_id):
        self.counters = self._get_counters(
            families, phenotype_info, draw_all_families,
            families_count_show_id)

    def to_dict(self):
        return OrderedDict([
            ('counters', [c.to_dict() for c in self.counters])
        ])

    def _families_to_dataframe(self, families, phenotype_column):
        families_records = []
        for family in families.values():
            members = family.members_in_order
            families_records +=\
                [(member.family_id, member.sex.name, member.role.name,
                  member.status, member.layout_position, member.generated,
                  member.get_attr(phenotype_column)) for member in members]
        return pd.DataFrame.from_records(
            families_records,
            columns=['family_id', 'sex', 'role', 'status', 'layout_position',
                     'generated', 'phenotype'])

    def _compare_families(self, first, second, phenotype_column):
        if len(first) != len(second):
            return False

        families = self._families_to_dataframe(
            OrderedDict([(first.family_id, first),
                         (second.family_id, second)]),
            phenotype_column)

        grouped_families = families.groupby(
            ['sex', 'role', 'status', 'generated', 'phenotype'])

        for _, group in grouped_families:
            family_group = group.groupby(['family_id'])
            if len(family_group.groups) == 2:
                if len(family_group.groups[first.family_id]) !=\
                        len(family_group.groups[second.family_id]):
                    return False
            else:
                return False

        return True

    def _get_unique_families_counters(self, families, phenotype_info):
        families_counters = OrderedDict()
        for family in families:
            is_family_in_counters = False
            for unique_family in families_counters.keys():
                if self._compare_families(
                        family, unique_family, phenotype_info.source):
                    is_family_in_counters = True
                    families_counters[unique_family].append(family.family_id)
                    break
            if not is_family_in_counters:
                families_counters[family] = [family.family_id]

        return families_counters

    def _get_all_families_counters(self, families):
        return OrderedDict([(family, family.family_id) for family in families])

    def _get_sorted_families_counters(
            self, families, phenotype_info, families_count_show_id):
        families_counters = self._get_unique_families_counters(
            families, phenotype_info)

        families_counters = OrderedDict(sorted(
            families_counters.items(), key=lambda fc: len(fc[1]),
            reverse=True))

        families_counters = OrderedDict([
            (family, (
                ', '.join(family_ids)
                if families_count_show_id is not None and
                families_count_show_id >= len(family_ids)
                else len(family_ids)))
            for family, family_ids in families_counters.items()
        ])

        return families_counters

    def _get_counters(
            self, families, phenotype_info, draw_all_families,
            families_count_show_id):
        if draw_all_families is True:
            families_counters = self._get_all_families_counters(families)
        else:
            families_counters = self._get_sorted_families_counters(
                families, phenotype_info, families_count_show_id)

        return [FamilyCounter(family, counter, phenotype_info)
                for family, counter in families_counters.items()]


class FamiliesCounters(object):

    def __init__(
            self, families, phenotype_info, draw_all_families,
            families_count_show_id):
        self.group_name = phenotype_info.name
        self.phenotypes = phenotype_info.get_phenotypes()
        self.counters = self._get_counters(
            families, phenotype_info, draw_all_families,
            families_count_show_id)
        self.legend = self._get_legend(phenotype_info)

    def to_dict(self):
        return OrderedDict([
            ('group_name', self.group_name),
            ('phenotypes', self.phenotypes),
            ('counters', [counter.to_dict() for counter in self.counters]),
            ('legend', self.legend)
        ])

    def _get_families_groups(self, families, phenotype_info):
        families_groups = defaultdict(list)

        for family in families.values():
            family_phenotypes =\
                frozenset(family.get_family_phenotypes(phenotype_info.source))
            family_phenotypes -= {phenotype_info.unaffected['name']}

            families_groups[family_phenotypes].append(family)

        families_groups_keys = sorted(list(families_groups.keys()), key=len)
        families_groups =\
            [families_groups[key] for key in families_groups_keys]

        return families_groups

    def _get_counters(
            self, families, phenotype_info, draw_all_families,
            families_count_show_id):

        families_groups =\
            self._get_families_groups(families, phenotype_info)

        return [FamiliesCounter(
            families, phenotype_info, draw_all_families,
            families_count_show_id)
                for families in families_groups]

    def _get_legend(self, phenotype_info):
        return list(phenotype_info.domain.values()) +\
            [phenotype_info.default] +\
            [phenotype_info.missing_person_info]
