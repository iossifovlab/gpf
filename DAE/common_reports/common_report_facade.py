from __future__ import unicode_literals

import os
import json


class CommonReportFacade(object):
    _common_report_cache = {}

    def __init__(self, common_reports_query_objects):
        self.query_objects_with_config =\
            common_reports_query_objects.query_objects_with_config

    def get_common_report(self, common_report_id):
        self.load_cache({common_report_id})

        if common_report_id not in self._common_report_cache:
            return None

        return self._common_report_cache[common_report_id]

    def get_all_common_reports(self):
        self.load_cache()

        return list(self._common_report_cache.values())

    def get_all_common_report_ids(self):
        return [
            config.id for config in self.query_objects_with_config.values()
        ]

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
        common_report_configs = list(filter(
            lambda config: (config.id == common_report_id),
            self.query_objects_with_config.values()))
        if len(common_report_configs) > 0:
            common_report_config = common_report_configs[0]
        else:
            return

        common_reports_path = common_report_config.path

        if not os.path.exists(common_reports_path):
            return

        with open(common_reports_path, 'r') as crf:
            common_report = json.load(crf)
        if common_report is None:
            return

        self._common_report_cache[common_report_id] = common_report
