import logging

from functools import cache

from dae.gene.denovo_gene_set_collection import DenovoGeneSetCollection
from dae.gene.denovo_gene_set_collection_factory import \
    DenovoGeneSetCollectionFactory

logger = logging.getLogger(__name__)

# TODO Document the denovo gene set spec somehow - what it contains,
# maybe make it a namedtuple subclass


class DenovoGeneSetsDb:
    """Class to manage available de Novo gene sets."""

    def __init__(self, gpf_instance):
        self.gpf_instance = gpf_instance
        self._gene_set_collections_cache = {}
        self._gene_set_configs_cache = {}

    def __len__(self):
        return len(self._denovo_gene_set_collections)

    def reload(self):
        self._gene_set_collections_cache = {}
        self._gene_set_configs_cache = {}

    @property
    def _denovo_gene_set_collections(self):
        if not self._gene_set_collections_cache:
            self._load_cache()
        return self._gene_set_collections_cache

    @property
    def _denovo_gene_set_configs(self):
        if not self._gene_set_configs_cache:
            self._load_cache()
        return self._gene_set_configs_cache

    def _load_cache(self):
        for study_id in self.get_genotype_data_ids():
            study = self.gpf_instance.get_genotype_data(study_id)
            assert study is not None, study_id

            gs_collection = \
                DenovoGeneSetCollectionFactory.load_collection(study)
            self._gene_set_configs_cache[study_id] = gs_collection.config
            self._gene_set_collections_cache[study_id] = gs_collection

    def _build_cache(self, genotype_data_ids):
        for study_id in genotype_data_ids:
            study = self.gpf_instance.get_genotype_data(study_id)
            assert study is not None, study_id
            DenovoGeneSetCollectionFactory.build_collection(study)

    def get_gene_set_descriptions(self, permitted_datasets=None):
        gene_sets_types = []
        for gs_id, gs_collection in self._denovo_gene_set_collections.items():
            if permitted_datasets is None or gs_id in permitted_datasets:
                gene_sets_types += gs_collection.get_gene_sets_types_legend()

        return {
            "desc": "Denovo",
            "name": "denovo",
            "format": ["key", " (|count|)"],
            "types": gene_sets_types,
        }

    @cache
    def get_genotype_data_ids(self):
        """Return list of genotype data IDs with denovo gene sets."""
        study_ids = set(
            self.gpf_instance.get_genotype_data_ids(local_only=True))
        result = set()
        for study_id in study_ids:
            config = self.gpf_instance.get_genotype_data_config(study_id)
            if config is None:
                logger.error(
                    "unable to load genotype data %s", study_id)
                raise ValueError(
                    f"unable to load genotype data {study_id}")

            if config.denovo_gene_sets and \
                    config.denovo_gene_sets.enabled and \
                    config.denovo_gene_sets.selected_person_set_collections:
                result.add(study_id)

        return result

    def get_gene_set_ids(self, genotype_data_id):
        return self._denovo_gene_set_configs[genotype_data_id].gene_sets_names

    def get_gene_set(
        self,
        gene_set_id,
        gene_set_spec,
        permitted_datasets=None,
        collection_id="denovo"  # pylint: disable=unused-argument
    ):
        """Return de Novo gene set matching the spec for permitted datasets."""
        gene_set_spec = self._filter_spec(gene_set_spec, permitted_datasets)

        return DenovoGeneSetCollection.get_gene_set(
            gene_set_id,
            list(self._denovo_gene_set_collections.values()),
            gene_set_spec,
        )

    def get_all_gene_sets(
        self,
        denovo_gene_set_spec,
        permitted_datasets=None,
        collection_id="denovo"  # pylint: disable=unused-argument
    ):
        """Return all de Novo gene sets matching the spec for permitted DS."""
        denovo_gene_set_spec = self._filter_spec(
            denovo_gene_set_spec, permitted_datasets
        )

        return DenovoGeneSetCollection.get_all_gene_sets(
            list(self._denovo_gene_set_collections.values()),
            denovo_gene_set_spec,
        )

    @staticmethod
    def _filter_spec(denovo_gene_set_spec, permitted_datasets):
        """Filter a denovo gene set spec to remove datasets without permitions.

        List of permitted datasets is passed and used to filter non-permitted
        dataset set from denovo gene set specicification.
        """
        return {
            genotype_data_id: {pg_id: v for pg_id, v in pg.items() if v}
            for genotype_data_id, pg in denovo_gene_set_spec.items()
            if permitted_datasets is None
            or genotype_data_id in permitted_datasets
        }
