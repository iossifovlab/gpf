import os
import json

from common_reports.config import CommonReportsConfigParser
from common_reports.common_report import CommonReport


class CommonReportFacade(object):

    def __init__(self, variants_db):
        self._common_report_cache = {}
        self._common_report_config_cache = {}

        self.variants_db = variants_db

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

        return [
            config.id for config in self._common_report_config_cache.values()
        ]

    def generate_common_report(self, common_report_id):
        self.load_cache({common_report_id})

        if common_report_id not in self._common_report_config_cache:
            return None

        study = self.variants_db.get_wdae_wrapper(common_report_id)
        common_report_config = \
            self._common_report_config_cache[common_report_id]
        file_path = common_report_config.file_path
        common_report = CommonReport(study, common_report_config)

        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, 'w+') as crf:
            json.dump(common_report.to_dict(), crf)

        self._load_common_report_in_cache(common_report_id)

    def generate_common_reports(self, common_report_ids=[]):
        for common_report_id in common_report_ids:
            self.generate_common_report(common_report_id)

    def generate_all_common_reports(self):
        for common_report_id in self.variants_db.get_all_ids():
            self.generate_common_report(common_report_id)

    def load_cache(self, common_report_ids=None):
        if common_report_ids is None:
            common_report_ids = set(self.variants_db.get_all_ids())

        assert isinstance(common_report_ids, set)

        cached_ids = set(self._common_report_config_cache.keys())
        if common_report_ids != cached_ids:
            to_load = common_report_ids - cached_ids
            for common_report_id in to_load:
                self._load_common_report_config_in_cache(common_report_id)
                self._load_common_report_in_cache(common_report_id)

    def _load_common_report_config_in_cache(self, common_report_id):
        common_report_config = CommonReportsConfigParser.parse(
            self.variants_db.get_config(common_report_id))
        if common_report_config is None:
            return

        self._common_report_config_cache[common_report_id] = \
            common_report_config

    def _load_common_report_in_cache(self, common_report_id):
        self._load_common_report_config_in_cache(common_report_id)

        if common_report_id not in self._common_report_config_cache:
            return

        common_report_config = \
            self._common_report_config_cache[common_report_id]

        common_reports_path = common_report_config.file_path

        if not os.path.exists(common_reports_path):
            return

        with open(common_reports_path, 'r') as crf:
            common_report = json.load(crf)
        if common_report is None:
            return

        self._common_report_cache[common_report_id] = common_report
