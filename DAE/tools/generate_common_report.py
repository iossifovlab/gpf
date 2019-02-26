#!/usr/bin/env python
import os

from configurable_entities.configuration import DAEConfig

from common_reports.common_report import CommonReportsGenerator
from common_reports.config import CommonReportsConfigs

from studies.dataset_facade import DatasetFacade
from studies.dataset_factory import DatasetFactory
from studies.dataset_definition import DirectoryEnabledDatasetsDefinition
from studies.study_facade import StudyFacade
from studies.study_definition import DirectoryEnabledStudiesDefinition


def main(dae_config=None):
    if dae_config is None:
        dae_config = DAEConfig()

    work_dir = dae_config.dae_data_dir
    studies_dir = dae_config.studies_dir
    datasets_dir = dae_config.datasets_dir

    study_definition = DirectoryEnabledStudiesDefinition(
        studies_dir, work_dir)
    study_facade = StudyFacade(study_definition)

    dataset_definitions = DirectoryEnabledDatasetsDefinition(
        study_facade, datasets_dir, work_dir)
    dataset_factory = DatasetFactory(study_facade)

    dataset_facade =\
        DatasetFacade(dataset_definitions, dataset_factory)

    common_reports_config = CommonReportsConfigs()
    common_reports_config.scan_directory(studies_dir, study_facade)
    common_reports_config.scan_directory(datasets_dir, dataset_facade)

    crg = CommonReportsGenerator(common_reports_config)
    crg.save_common_reports()


if __name__ == '__main__':
    main()
