from dae.configuration.dae_config_parser import DAEConfigParser

from dae.studies.variants_db import VariantsDb

from dae.common_reports.common_report_facade import CommonReportFacade

from dae.gene.gene_info_config import GeneInfoConfigParser
from dae.gene.scores import ScoreLoader
from dae.gene.weights import WeightsLoader
from dae.gene.score_config_parser import ScoreConfigParser

from dae.gene.gene_set_collections import GeneSetsCollections
from dae.gene.denovo_gene_set_facade import DenovoGeneSetFacade

from dae.enrichment_tool.background_facade import BackgroundFacade

from .models import Dataset

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
            dae_config = DAEConfigParser.read_and_parse_file_configuration()
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

        score_config = ScoreConfigParser.read_and_parse_file_configuration(
            self.dae_config.genomic_scores_db.conf_file,
            self.dae_config.dae_data_dir
        )
        self.score_loader = ScoreLoader(score_config)

        self.gene_info_config = \
            GeneInfoConfigParser.read_and_parse_file_configuration(
                self.dae_config.gene_info_db.conf_file,
                self.dae_config.dae_data_dir
            )
        self.weights_loader = WeightsLoader(
            config=self.gene_info_config.gene_weights)

        self.gene_sets_collections = GeneSetsCollections(
            self.vdb, self.gene_info_config)
        self.denovo_gene_set_facade = DenovoGeneSetFacade(self.vdb)

        self.background_facade = BackgroundFacade(self.vdb)

    def get_variants_db(self):
        if self.vdb is None:
            self.reload_dataset()
            assert self.vdb is not None
            assert self.common_reports is not None

        return self.vdb

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

    def get_denovo_gene_set_facade(self):
        self.get_variants_db()
        return self.denovo_gene_set_facade

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
