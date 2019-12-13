from collections import OrderedDict

from dae.common_reports.people_counter import PeopleCounters
from dae.common_reports.family_counter import FamiliesGroupCounters


class FamiliesReport(object):

    def __init__(
            self, genotype_data_study, people_groups_info, filter_objects,
            draw_all_families=False, families_count_show_id=False):
        self.families = genotype_data_study.families
        self.people_groups_info = people_groups_info
        self.filter_objects = filter_objects
        self.draw_all_families = draw_all_families
        self.families_count_show_id = families_count_show_id

        self.families_total = len(self.families.values())
        self.people_counters = self._get_people_counters()
        self.families_counters = self._get_families_counters()

    def to_dict(self):
        return OrderedDict([
            ('families_total', self.families_total),
            ('people_counters', [pc.to_dict() for pc in self.people_counters]),
            ('families_counters',
             [fc.to_dict() for fc in self.families_counters])
        ])

    def _get_people_counters(self):
        return [
            PeopleCounters(self.families, filter_object)
            for filter_object in self.filter_objects
        ]

    def _get_families_counters(self):
        return [
            FamiliesGroupCounters(
                self.families, people_group_info, self.draw_all_families,
                self.families_count_show_id)
            for people_group_info in self.people_groups_info.people_groups_info
        ]
