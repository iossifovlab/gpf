from __future__ import unicode_literals

import os
import json

from common_reports.config import CommonReportsConfigs

from studies.dataset_facade import DatasetFacade
from studies.dataset_factory import DatasetFactory
from studies.dataset_definition import DirectoryEnabledDatasetsDefinition
from studies.study_facade import StudyFacade
from studies.study_definition import DirectoryEnabledStudiesDefinition


class CommonReportFacade(object):
    _common_report_cache = {}

    def __init__(self):
        work_dir = os.environ.get("DAE_DB_DIR")
        config_file = os.environ.get("DAE_DATA_DIR")
        studies_dir = os.path.join(config_file, 'studies')
        datasets_dir = os.path.join(config_file, 'datasets')

        study_definition = DirectoryEnabledStudiesDefinition(
            studies_dir, work_dir)
        study_facade = StudyFacade(study_definition)

        dataset_definitions = DirectoryEnabledDatasetsDefinition(
            study_facade, datasets_dir, work_dir)
        dataset_factory = DatasetFactory(study_facade)

        dataset_facade =\
            DatasetFacade(dataset_definitions, dataset_factory)

        self.configs = CommonReportsConfigs()
        self.configs.scan_directory(studies_dir, study_facade)
        self.configs.scan_directory(datasets_dir, dataset_facade)

    def get_common_report(self, common_report_id):
        self.load_cache({common_report_id})

        if common_report_id not in self._common_report_cache:
            return None

        return self._common_report_cache[common_report_id]

    def get_all_common_reports(self):
        self.load_cache()

        return list(self._common_report_cache.values())

    def get_all_common_report_ids(self):
        return [crc.id for crc in self.configs.common_reports_configs]

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
        common_reports = list(filter(
            lambda config: config.id == common_report_id,
            self.configs.common_reports_configs))
        if len(common_reports) > 0:
            common_report = common_reports[0]
        else:
            return

        common_reports_path = common_report.path

        if not os.path.exists(common_reports_path):
            return

        with open(common_reports_path, 'r') as crf:
            common_report = json.load(crf)
        if common_report is None:
            return

        common_report['id'] = common_report_id

        self._common_report_cache[common_report_id] = common_report
