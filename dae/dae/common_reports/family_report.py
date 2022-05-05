from dae.common_reports.family_counter import FamiliesGroupCounters


class FamiliesReport(object):
    def __init__(self, json):
        families_counters = [
            FamiliesGroupCounters(fc) for fc in json
        ]
        self.families_counters = {
            fc.group_name: fc for fc in families_counters
        }

    @staticmethod
    def from_genotype_study(genotype_data_study, person_set_collections):
        families = genotype_data_study.families
        config = genotype_data_study.config.common_report
        families_counters = [
            FamiliesGroupCounters.from_families(
                families,
                person_set_collection,
                config.draw_all_families,
                config.families_count_show_id
            )
            for person_set_collection in person_set_collections
        ]
        return FamiliesReport([
            fc.to_dict(full=True) for fc in families_counters
        ])

    def to_dict(self, full=False):
        return [
            fc.to_dict(full=full) for fc in self.families_counters.values()
        ]
