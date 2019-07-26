from configurable_entities.configuration import DAEConfig

from studies.factory import VariantsDb

from common_reports.common_report_facade import CommonReportFacade

from gene.config import GeneInfoConfig
from gene.scores import ScoreLoader
from gene.weights import WeightsLoader

from gene.gene_set_collections import GeneSetsCollections
from gene.denovo_gene_set_collection_facade import \
    DenovoGeneSetCollectionFacade

from enrichment_tool.background_facade import BackgroundFacade

from datasets_api.models import Dataset

from threading import Lock


__all__ = ['get_studies_manager']


class CommonReportsManager(object):

    def __init__(self, dae_config, vdb):
        self.dae_config = dae_config
        self.vdb = vdb

        self.common_report_facade = CommonReportFacade(self.vdb)


class StudiesManager(object):

    def __init__(self, dae_config=None):
        if dae_config is None:
            dae_config = DAEConfig()
        self.dae_config = dae_config
        self.vdb = None

        self.score_loader = None
        self.gene_info_config = None
        self.weights_loader = None

        self.gene_sets_collections = None
        self.common_reports = None

    def reload_dataset(self):
        self.vdb = VariantsDb(self.dae_config)
        self.common_reports = CommonReportsManager(self.dae_config, self.vdb)

        for study_id in self.vdb.get_all_ids():
            Dataset.recreate_dataset_perm(study_id, [])

        self.score_loader = ScoreLoader(daeConfig=self.dae_config)
        self.gene_info_config = GeneInfoConfig.from_config(self.dae_config)
        self.weights_loader = WeightsLoader(config=self.gene_info_config)

        self.gene_sets_collections = GeneSetsCollections(
            self.vdb, self.gene_info_config)
        self.denovo_gene_set_collection_facade = \
            DenovoGeneSetCollectionFacade(self.vdb)

        self.background_facade = BackgroundFacade(self.vdb)

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

    def get_gene_info_config(self):
        self.get_variants_db()
        return self.gene_info_config

    def get_score_loader(self):
        self.get_variants_db()
        assert self.score_loader is not None
        return self.score_loader

    def get_weights_loader(self):
        self.get_variants_db()
        return self.weights_loader

    def get_gene_sets_collections(self):
        self.get_variants_db()
        return self.gene_sets_collections

    def get_denovo_gene_set_collection_facade(self):
        self.get_variants_db()
        return self.denovo_gene_set_collection_facade

    def get_background_facade(self):
        self.get_variants_db()
        return self.background_facade


_studies_manager = None
_studies_manager_lock = Lock()


def get_studies_manager():
    global _studies_manager
    global _studies_manager_lock

    if _studies_manager is None:
        _studies_manager_lock.acquire()
        try:
            if _studies_manager is None:
                sm = StudiesManager()
                sm.reload_dataset()
                _studies_manager = sm
        finally:
            _studies_manager_lock.release()

    return _studies_manager
