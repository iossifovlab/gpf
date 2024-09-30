import logging
from collections.abc import Iterable
from functools import lru_cache
from typing import Any, cast

from dae.gene_sets.denovo_gene_set_collection import DenovoGeneSetCollection
from dae.gene_sets.denovo_gene_set_helpers import (
    DenovoGeneSetHelpers,
)

logger = logging.getLogger(__name__)


class DenovoGeneSetsDb:
    """Class to manage available de Novo gene sets."""

    def __init__(self, gpf_instance: Any):
        self.gpf_instance = gpf_instance
        self._gene_set_collections_cache: dict[
            str, DenovoGeneSetCollection] = {}
        self._gene_set_configs_cache: dict[str, Any] = {}

    def __len__(self) -> int:
        return len(self._denovo_gene_set_collections)

    def reload(self) -> None:
        self._gene_set_collections_cache = {}
        self._gene_set_configs_cache = {}

    @property
    def _denovo_gene_set_collections(
            self) -> dict[str, DenovoGeneSetCollection]:
        if not self._gene_set_collections_cache:
            self._load_cache()
        return self._gene_set_collections_cache

    @property
    def _denovo_gene_set_configs(self) -> dict[str, Any]:
        if not self._gene_set_configs_cache:
            self._load_cache()
        return self._gene_set_configs_cache

    def _load_cache(self) -> None:
        for study_id in self.get_genotype_data_ids():
            study = self.gpf_instance.get_genotype_data(study_id)
            assert study is not None, study_id

            gs_collection = \
                DenovoGeneSetHelpers.load_collection(study)
            self._gene_set_configs_cache[study_id] = gs_collection.config
            self._gene_set_collections_cache[study_id] = gs_collection

    def _build_cache(self, genotype_data_ids: list[str]) -> None:
        for study_id in genotype_data_ids:
            study = self.gpf_instance.get_genotype_data(study_id)
            assert study is not None, study_id
            DenovoGeneSetHelpers.build_collection(study)

    def get_gene_set_descriptions(
        self, permitted_datasets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return gene set descriptions for permitted datasets."""
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

    def get_collection_types_legend(self, gs_collection_id: str) -> list[Any]:
        return self._denovo_gene_set_collections[gs_collection_id]\
            .get_gene_sets_types_legend()

    @lru_cache(maxsize=64)
    def get_genotype_data_ids(self) -> set[str]:
        """Return list of genotype data IDs with denovo gene sets."""
        study_ids = set(
            self.gpf_instance.get_genotype_data_ids())
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

    def get_gene_set_ids(self, genotype_data_id: str) -> list[str]:
        return cast(
            list[str],
            self._gene_set_configs_cache[
                genotype_data_id].gene_sets_names)

    def get_gene_set(
        self,
        gene_set_id: str,
        gene_set_spec: dict[str, dict[str, list[str]]],
        permitted_datasets: Iterable[str] | None = None,
        collection_id: str = "denovo",  # noqa: ARG002
    ) -> dict[str, Any] | None:
        # pylint: disable=unused-argument
        """Return de Novo gene set matching the spec for permitted datasets."""
        gene_set_spec = self._filter_spec(gene_set_spec, permitted_datasets)

        return DenovoGeneSetCollection.get_gene_set_from_collections(
            gene_set_id,
            list(self._denovo_gene_set_collections.values()),
            gene_set_spec,
        )

    def get_all_gene_sets(
        self,
        denovo_gene_set_spec: dict[str, dict[str, list[str]]],
        permitted_datasets: list[str] | None = None,
        collection_id: str = "denovo",  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        # pylint: disable=unused-argument
        """Return all de Novo gene sets matching the spec for permitted DS."""
        denovo_gene_set_spec = self._filter_spec(
            denovo_gene_set_spec, permitted_datasets,
        )

        return DenovoGeneSetCollection.get_all_gene_sets(
            list(self._denovo_gene_set_collections.values()),
            denovo_gene_set_spec,
        )

    @staticmethod
    def _filter_spec(
        denovo_gene_set_spec: dict[str, dict[str, list[str]]],
        permitted_datasets: Iterable[str] | None = None,
    ) -> dict[str, dict[str, list[str]]]:
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
