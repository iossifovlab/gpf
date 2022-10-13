import logging

from functools import cache

from dae.gene.denovo_gene_set_collection import DenovoGeneSetCollection
from dae.gene.denovo_gene_set_collection_factory import \
    DenovoGeneSetCollectionFactory

logger = logging.getLogger(__name__)

# TODO Document the denovo gene set spec somehow - what it contains,
# maybe make it a namedtuple subclass


class DenovoGeneSetsDb:
    def __init__(self, gpf_instance):
        self.gpf_instance = gpf_instance
        self._denovo_gene_set_collections_cache = dict()
        self._denovo_gene_set_configs_cache = dict()

    def __len__(self):
        return len(self._denovo_gene_set_collections)

    @property
    def _denovo_gene_set_collections(self):
        if not self._denovo_gene_set_collections_cache:
            self._load_cache()
        return self._denovo_gene_set_collections_cache

    @property
    def _denovo_gene_set_configs(self):
        if not self._denovo_gene_set_configs_cache:
            self._load_cache()
        return self._denovo_gene_set_configs_cache

    def _load_cache(self):
        for genotype_data_id in self.get_genotype_data_ids():
            genotype_data_study = \
                self.gpf_instance.get_genotype_data(genotype_data_id)
            assert genotype_data_study is not None, genotype_data_id

            denovo_gene_set_collection = \
                DenovoGeneSetCollectionFactory.load_collection(
                    genotype_data_study)

            self._denovo_gene_set_configs_cache[
                genotype_data_id
            ] = denovo_gene_set_collection.config
            self._denovo_gene_set_collections_cache[
                genotype_data_id
            ] = denovo_gene_set_collection

    def _build_cache(self, genotype_data_ids):
        for genotype_data_id in genotype_data_ids:
            genotype_data_study = \
                self.gpf_instance.get_genotype_data(genotype_data_id)
            assert genotype_data_study is not None, genotype_data_id
            DenovoGeneSetCollectionFactory.build_collection(
                genotype_data_study
            )

    def get_gene_set_descriptions(self, permitted_datasets=None):
        gene_sets_types = []
        for (
            denovo_gene_set_id,
            denovo_gene_set_collection,
        ) in self._denovo_gene_set_collections.items():
            if (
                permitted_datasets is None
                or denovo_gene_set_id in permitted_datasets
            ):
                gene_sets_types += (
                    denovo_gene_set_collection.get_gene_sets_types_legend()
                )

        return {
            "desc": "Denovo",
            "name": "denovo",
            "format": ["key", " (|count|)"],
            "types": gene_sets_types,
        }

    @cache
    def get_genotype_data_ids(self):
        genotype_data_ids = set(
            self.gpf_instance.get_genotype_data_ids(local_only=True)
        )
        result = set()
        for genotype_data_id in genotype_data_ids:
            gtd_config = \
                self.gpf_instance.get_genotype_data_config(genotype_data_id)
            if gtd_config is None:
                logger.error(
                    "unable to load genotype data %s", genotype_data_id)
                raise ValueError(
                    f"unable to load genotype data {genotype_data_id}")

            if (
                gtd_config.denovo_gene_sets
                and gtd_config.denovo_gene_sets.enabled
                and gtd_config.denovo_gene_sets.selected_person_set_collections
            ):
                result.add(genotype_data_id)

        return result

    def get_gene_set_ids(self, genotype_data_id):
        return self._denovo_gene_set_configs[genotype_data_id].gene_sets_names

    def get_gene_set(
        self, gene_set_id, denovo_gene_set_spec, permitted_datasets=None
    ):
        denovo_gene_set_spec = self._filter_spec(
            denovo_gene_set_spec, permitted_datasets
        )

        return DenovoGeneSetCollection.get_gene_set(
            gene_set_id,
            list(self._denovo_gene_set_collections.values()),
            denovo_gene_set_spec,
        )

    def get_all_gene_sets(self, denovo_gene_set_spec, permitted_datasets=None):
        denovo_gene_set_spec = self._filter_spec(
            denovo_gene_set_spec, permitted_datasets
        )

        return DenovoGeneSetCollection.get_all_gene_sets(
            list(self._denovo_gene_set_collections.values()),
            denovo_gene_set_spec,
        )

    @staticmethod
    def _filter_spec(denovo_gene_set_spec, permitted_datasets):
        """
        Filter a denovo gene set spec to remove datasets which
        are not permitted for access and person set collections with no
        specified values.
        """
        return {
            genotype_data_id: {pg_id: v for pg_id, v in pg.items() if v}
            for genotype_data_id, pg in denovo_gene_set_spec.items()
            if permitted_datasets is None
            or genotype_data_id in permitted_datasets
        }
