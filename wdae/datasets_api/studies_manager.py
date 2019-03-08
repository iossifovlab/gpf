from __future__ import unicode_literals
from builtins import object

from configurable_entities.configuration import DAEConfig

from studies.factory import VariantsDb
from common_reports.config import CommonReportsQueryObjects
from common_reports.common_report import CommonReportsGenerator
from common_reports.common_report_facade import CommonReportFacade

from gene.scores import ScoreLoader
from gene.weights import WeightsLoader

from gene.gene_set_collections import GeneSetsCollections

from datasets_api.models import Dataset


__all__ = ['get_studies_manager']


class CommonReportsManager(object):

    def __init__(self, dae_config, vdb):
        self.dae_config = dae_config
        self.vdb = vdb

        self.common_reports_query_objects = CommonReportsQueryObjects(
            self.vdb.study_facade, self.vdb.dataset_facade)
        self.common_reports_generator = CommonReportsGenerator(
            self.common_reports_query_objects)
        self.common_report_facade = CommonReportFacade(
            self.common_reports_query_objects)


class StudiesManager(object):

    def __init__(self, dae_config=None):
        if dae_config is None:
            dae_config = DAEConfig()
        self.dae_config = dae_config
        self.vdb = None

        self.score_loader = None
        self.weights_loader = None

        self.gene_sets_collections = None

    def reload_dataset(self):
        self.vdb = VariantsDb(self.dae_config)
        self.common_reports = CommonReportsManager(self.dae_config, self.vdb)

        for dataset_id in self.vdb.get_datasets_ids():
            Dataset.recreate_dataset_perm(dataset_id, [])

        self.score_loader = ScoreLoader()
        self.weights_loader = WeightsLoader()

        self.gene_sets_collections = GeneSetsCollections(self.vdb)

    def get_variants_db(self):
        if self.vdb is None:
            self.reload_dataset()
            assert self.vdb is not None
            assert self.common_reports is not None

        return self.vdb

    def get_dataset_facade(self):
        return self.get_variants_db().dataset_facade

    def get_common_report_facade(self):
        self.get_variants_db()
        return self.common_reports.common_report_facade

    def get_score_loader(self):
        self.get_variants_db()
        return self.score_loader

    def get_weights_loader(self):
        self.get_variants_db()
        return self.weights_loader

    def get_gene_sets_collections(self):
        self.get_variants_db()
        return self.gene_sets_collections


_studies_manager = None


def get_studies_manager():
    global _studies_manager
    if _studies_manager is None:
        _studies_manager = StudiesManager()
    return _studies_manager
