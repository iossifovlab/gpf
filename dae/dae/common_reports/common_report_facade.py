import os
import json

from dae.common_reports.common_report import CommonReport

from dae.utils.dae_utils import join_line


class CommonReportFacade(object):
    def __init__(self, gpf_instance):
        self._common_report_cache = {}
        self._common_report_config_cache = {}

        self.gpf_instance = gpf_instance

    def get_common_report(self, common_report_id):
        self.load_cache({common_report_id})

        if common_report_id not in self._common_report_cache:
            return None

        return self._common_report_cache[common_report_id]

    def get_all_common_reports(self):
        self.load_cache()

        return list(self._common_report_cache.values())

    def get_common_report_config(self, common_report_id):
        self.load_cache({common_report_id})

        if common_report_id not in self._common_report_config_cache:
            return None

        return self._common_report_config_cache[common_report_id]

    def get_all_common_report_configs(self):
        self.load_cache()

        return list(self._common_report_config_cache.values())

    def get_all_common_report_ids(self):
        self.load_cache()

        return list(self._common_report_config_cache.keys())

    def generate_common_report(self, common_report_id):
        self.load_cache({common_report_id})

        if common_report_id not in self._common_report_config_cache:
            return None

        genotype_data_study = \
            self.gpf_instance.get_genotype_data(common_report_id)
        common_report_config = self._common_report_config_cache[
            common_report_id
        ]
        file_path = common_report_config.file_path
        common_report = CommonReport(genotype_data_study, common_report_config)

        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, "w+") as crf:
            json.dump(common_report.to_dict(), crf)

        self._load_common_report_in_cache(common_report_id)

    def generate_common_reports(self, common_report_ids=[]):
        for common_report_id in common_report_ids:
            self.generate_common_report(common_report_id)

    def generate_all_common_reports(self):
        for common_report_id in self.gpf_instance.get_genotype_data_ids():
            self.generate_common_report(common_report_id)

    def get_families_data(self, genotype_data):
        # FIXME: start using FamiliesData save method
        if not genotype_data:
            return None

        data = []
        data.append(
            [
                "familyId",
                "personId",
                "dadId",
                "momId",
                "sex",
                "status",
                "role",
                "genotype_data_study",
            ]
        )

        families = list(genotype_data.families.values())
        families.sort(key=lambda f: f.family_id)
        for f in families:
            for p in f.members_in_order:

                row = [
                    p.family_id,
                    p.person_id,
                    p.mom_id if p.mom_id else "0",
                    p.dad_id if p.dad_id else "0",
                    p.sex,
                    p.status,
                    p.role,
                    genotype_data.name,
                ]

                data.append(row)

        return map(join_line, data)

    def load_cache(self, common_report_ids=None):
        if common_report_ids is None:
            common_report_ids = set(self.gpf_instance.get_genotype_data_ids())

        assert isinstance(common_report_ids, set)

        cached_ids = set(self._common_report_config_cache.keys())
        if common_report_ids != cached_ids:
            to_load = common_report_ids - cached_ids
            for common_report_id in to_load:
                self._load_common_report_in_cache(common_report_id)

    def _load_common_report_config_in_cache(self, common_report_id):
        genotype_data_config = self.gpf_instance.get_genotype_data_config(
            common_report_id
        )

        if genotype_data_config is None:
            return

        common_report_config = genotype_data_config.common_report

        if not common_report_config.enabled:
            return

        self._common_report_config_cache[
            common_report_id
        ] = common_report_config

    def _load_common_report_in_cache(self, common_report_id):
        self._load_common_report_config_in_cache(common_report_id)

        if common_report_id not in self._common_report_config_cache:
            return

        common_report_config = self._common_report_config_cache[
            common_report_id
        ]

        common_reports_path = common_report_config.file_path

        if not common_reports_path or not os.path.exists(common_reports_path):
            return

        with open(common_reports_path, "r") as crf:
            common_report = json.load(crf)
        if common_report is None:
            return

        self._common_report_cache[common_report_id] = common_report

    def query_person_counters(
            self,
            common_report_id,
            person_set_collection_id,
            person_set_id,
            sex=None):

        genotype_data_study = \
            self.gpf_instance._variants_db.get(common_report_id)
        collections = genotype_data_study.person_set_collections
        person_sets = collections[person_set_collection_id].person_sets
        print("person_sets:", person_sets)

        if person_set_id not in person_sets:
            return []

        person_set = person_sets[person_set_id]

        if sex:
            return list(filter(
                lambda p: p.sex == sex, person_set.persons.values()
            ))
        else:
            return list(person_set.persons.values())

    def query_denovo_reports(
        self,
        common_report_id,
        person_set_collection_id,
        person_set_id,
        effect_type
    ):
        self.load_cache({common_report_id})
        genotype_data_study = \
            self.gpf_instance._variants_db.get(common_report_id)
        common_report_config = self._common_report_config_cache[
            common_report_id
        ]
        common_report = CommonReport(genotype_data_study, common_report_config)
        denovo_report = common_report.denovo_report

        for table in denovo_report.tables:
            if table.person_set_collection.id == person_set_collection_id:
                for effect_row in table.rows:
                    if effect_row.effect_type == effect_type:
                        for cell in effect_row.row:
                            if cell.person_set.id == person_set_id:
                                return cell.to_dict()
