from collections import OrderedDict

from dae.common_reports.people_counter import PeopleCounters
from dae.common_reports.family_counter import FamiliesGroupCounters


class FamiliesReport(object):
    def __init__(
        self,
        families,
        person_set_collections,
        draw_all_families=False,
        families_count_show_id=False,
    ):

        self.families = families

        self.person_set_collections = person_set_collections
        self.draw_all_families = draw_all_families
        self.families_count_show_id = families_count_show_id

        self.families_total = len(self.families.values())
        self.people_counters = self._get_people_counters()
        self.families_counters = self._build_families_counters()

    def to_dict(self):
        return OrderedDict(
            [
                ("families_total", self.families_total),
                (
                    "people_counters",
                    [pc.to_dict() for pc in self.people_counters],
                ),
                (
                    "families_counters",
                    [fc.to_dict() for fc in self.families_counters],
                ),
            ]
        )

    def _get_people_counters(self):
        return [
            PeopleCounters(self.families, person_set_collection)
            for person_set_collection in self.person_set_collections
        ]

    def _build_families_counters(self):
        result = [
            FamiliesGroupCounters(
                self.families,
                person_set_collection,
                self.draw_all_families,
                self.families_count_show_id,
            )
            for person_set_collection in self.person_set_collections
        ]

        return result
