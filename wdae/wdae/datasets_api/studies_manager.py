from dae.gpf_instance.gpf_instance import GPFInstance

from dae.gene.gene_info_config import GeneInfoConfigParser
from dae.gene.scores import ScoresFactory
from dae.gene.weights import WeightsFactory
from dae.gene.score_config_parser import ScoreConfigParser

from dae.gene.gene_set_collections import GeneSetsCollections
from dae.gene.denovo_gene_set_facade import DenovoGeneSetFacade

from dae.enrichment_tool.background_facade import BackgroundFacade

from .models import Dataset

from threading import Lock


__all__ = ['get_studies_manager']


class StudiesManager(object):

    def __init__(self, gpf_instance=None):
        if gpf_instance is None:
            gpf_instance = GPFInstance()
        self.gpf_instance = gpf_instance

        self.dae_config = gpf_instance.dae_config
        self.vdb = None

        self.scores_factory = None
        self.gene_info_config = None
        self.weights_factory = None

        self.gene_sets_collections = None
        self.common_report_facade = gpf_instance.common_report_facade

    def reload_dataset(self):
        self.vdb = self.gpf_instance.variants_db

        for study_id in self.vdb.get_all_ids():
            Dataset.recreate_dataset_perm(study_id, [])

        score_config = ScoreConfigParser.read_and_parse_file_configuration(
            self.dae_config.genomic_scores_db.conf_file,
            self.dae_config.dae_data_dir
        )
        self.scores_factory = ScoresFactory(score_config)

        self.gene_info_config = \
            GeneInfoConfigParser.read_and_parse_file_configuration(
                self.dae_config.gene_info_db.conf_file,
                self.dae_config.dae_data_dir
            )
        self.weights_factory = WeightsFactory(
            config=self.gene_info_config.gene_weights)

        self.gene_sets_collections = GeneSetsCollections(
            self.vdb, self.gene_info_config)
        self.denovo_gene_set_facade = DenovoGeneSetFacade(self.vdb)

        self.background_facade = BackgroundFacade(self.vdb)

    def get_variants_db(self):
        if self.vdb is None:
            self.reload_dataset()
            assert self.vdb is not None
            assert self.common_report_facade is not None

        return self.vdb

    def get_common_report_facade(self):
        self.get_variants_db()
        return self.common_report_facade

    def get_gene_info_config(self):
        self.get_variants_db()
        return self.gene_info_config

    def get_scores_factory(self):
        self.get_variants_db()
        assert self.scores_factory is not None
        return self.scores_factory

    def get_weights_factory(self):
        self.get_variants_db()
        return self.weights_factory

    def get_gene_sets_collections(self):
        self.get_variants_db()
        return self.gene_sets_collections

    def get_denovo_gene_set_facade(self):
        self.get_variants_db()
        return self.denovo_gene_set_facade

    def get_background_facade(self):
        self.get_variants_db()
        return self.background_facade

    def get_permission_denied_prompt(self):
        return self.dae_config.gpfjs.permission_denied_prompt


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
