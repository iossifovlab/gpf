import logging
import operator
from functools import cached_property, lru_cache
from typing import Any, cast

from dae.gene_sets.denovo_gene_set_collection import DenovoGeneSetCollection
from dae.gene_sets.denovo_gene_set_helpers import (
    DenovoGeneSetHelpers,
)
from dae.gene_sets.denovo_gene_sets_config import (
    parse_denovo_gene_sets_study_config,
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

    def has_gene_sets(self) -> bool:
        return len(self._denovo_gene_set_collections) > 0

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

            dgsc = DenovoGeneSetHelpers.load_collection(study)
            if dgsc is None:
                logger.info(
                    "No denovo gene set collection for %s", study_id)
                continue

            self._gene_set_configs_cache[study_id] = dgsc.config
            self._gene_set_collections_cache[study_id] = dgsc

    def build_cache(
        self, genotype_data_ids: list[str], *,
        force: bool = False,
    ) -> None:
        """Build cache for de Novo gene sets for specified genotype data IDs."""
        for study_id in genotype_data_ids:
            study = self.gpf_instance.get_genotype_data(study_id)
            assert study is not None, study_id
            DenovoGeneSetHelpers.build_collection(study, force=force)

    @cached_property
    def collections_descriptions(self) -> list[dict[str, Any]]:
        """Return gene set descriptions."""

        return [{
            "desc": "Denovo",
            "name": "denovo",
            "format": ["key", " (|count|)"],
        }]

    @cached_property
    def denovo_gene_sets_types(self) -> list[dict[str, Any]]:
        """Return denovo gene sets types descriptions."""
        return sorted([
            gs_collection.get_gene_sets_types_legend()
            for gs_collection in self._denovo_gene_set_collections.values()
        ], key=operator.itemgetter("datasetId"))

    def get_collection_types_legend(
        self, gs_collection_id: str,
    ) -> dict[str, Any]:
        return self._denovo_gene_set_collections[gs_collection_id]\
            .get_gene_sets_types_legend()

    @lru_cache(maxsize=64)
    def get_genotype_data_ids(self) -> set[str]:
        """Return list of genotype data IDs with denovo gene sets."""
        study_ids = set(
            self.gpf_instance.get_genotype_data_ids())
        result = set()
        for study_id in study_ids:
            study = self.gpf_instance.get_genotype_data(study_id)
            study_config = study.config
            if study_config is None:
                logger.error(
                    "unable to load genotype data %s", study_id)
                raise ValueError(
                    f"unable to load genotype data {study_id}")
            psc_config = parse_denovo_gene_sets_study_config(
                study_config,
                has_denovo=study.has_denovo,
            )
            if psc_config is not None:
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
        collection_id: str = "denovo",  # noqa: ARG002
    ) -> dict[str, Any] | None:
        # pylint: disable=unused-argument
        """Return de Novo gene set matching the spec for permitted datasets."""
        return DenovoGeneSetCollection.get_gene_set_from_collections(
            gene_set_id,
            list(self._denovo_gene_set_collections.values()),
            gene_set_spec,
        )

    def get_all_gene_sets(
        self,
        denovo_gene_set_spec: dict[str, dict[str, list[str]]],
        collection_id: str = "denovo",  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        # pylint: disable=unused-argument
        """Return all de Novo gene sets matching the spec for permitted DS."""
        return DenovoGeneSetCollection.get_all_gene_sets(
            list(self._denovo_gene_set_collections.values()),
            denovo_gene_set_spec,
        )
