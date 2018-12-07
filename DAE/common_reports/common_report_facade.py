import os
import json

from common_reports.config import CommonReportsConfig
from studies.default_settings import get_config as get_studies_config
from study_groups.default_settings import get_config as get_study_groups_config


class CommonReportFacade(object):
    _common_report_cache = {}

    def __init__(self):
        self.config = CommonReportsConfig()

    def get_common_report(self, common_report_id):
        self.load_cache({common_report_id})

        if common_report_id not in self._common_report_cache:
            return None

        return self._common_report_cache[common_report_id]

    def get_all_common_reports(self):
        self.load_cache()

        return list(self._common_report_cache.values())

    def get_all_common_report_ids(self):
        return list(self.config.studies().keys()) +\
            list(self.config.study_groups().keys())

    def load_cache(self, common_report_ids=None):
        if common_report_ids is None:
            common_report_ids = set(self.get_all_common_report_ids())

        assert isinstance(common_report_ids, set)

        cached_ids = set(self._common_report_cache.keys())
        if common_report_ids != cached_ids:
            to_load = common_report_ids - cached_ids
            for common_report_id in to_load:
                self._load_common_report_in_cache(common_report_id)

    def _load_common_report_in_cache(self, common_report_id):
        if common_report_id in self.config.studies().keys():
            common_reports_dir = get_studies_config().get('COMMON_REPORTS_DIR')
        elif common_report_id in self.config.study_groups().keys():
            common_reports_dir = get_study_groups_config()\
                .get('COMMON_REPORTS_DIR')
        else:
            return

        with open(os.path.join(
                common_reports_dir, common_report_id + '.json'), 'r') as crf:
            common_report = json.load(crf)
        if common_report is None:
            return

        self._common_report_cache[common_report_id] = common_report
