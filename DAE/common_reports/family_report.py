from __future__ import unicode_literals
from __future__ import division

from collections import OrderedDict

from common_reports.people_counter import PeopleCounters
from common_reports.family_counter import FamiliesCounters


class FamiliesReport(object):

    def __init__(
            self, query_object, phenotypes_info, filter_objects,
            draw_all_families=False, families_count_show_id=False):
        families = query_object.families

        self.families_total = len(families)
        self.people_counters =\
            self._get_people_counters(families, filter_objects)
        self.families_counters = self._get_families_counters(
            families, phenotypes_info, draw_all_families,
            families_count_show_id)

    def to_dict(self):
        return OrderedDict([
            ('families_total', self.families_total),
            ('people_counters', [pc.to_dict() for pc in self.people_counters]),
            ('families_counters',
             [fc.to_dict() for fc in self.families_counters])
        ])

    def _get_people_counters(self, families, filter_objects):
        return [
            PeopleCounters(families, filter_object)
            for filter_object in filter_objects
        ]

    def _get_families_counters(
            self, families, phenotypes_info, draw_all_families,
            families_count_show_id):
        return [
            FamiliesCounters(families, phenotype_info, draw_all_families,
                             families_count_show_id)
            for phenotype_info in phenotypes_info.phenotypes_info
        ]
