import logging
from collections.abc import Generator
from functools import cached_property
from typing import Any, cast

from studies.response_transformer import ResponseTransformer
from studies.study_wrapper import StudyWrapperBase

from dae.pedigrees.families_data import FamiliesData
from dae.person_sets import PersonSetCollection
from federation.remote_phenotype_data import RemotePhenotypeData
from federation.remote_study import RemoteGenotypeData
from federation.remote_variant import QUERY_SOURCES, RemoteFamilyVariant

logger = logging.getLogger(__name__)


class RemoteStudyWrapper(StudyWrapperBase):
    """Wrapper class for remote (federation) studies."""

    def __init__(self, remote_genotype_data: RemoteGenotypeData):
        self.remote_genotype_data = remote_genotype_data
        self.remote_study_id = remote_genotype_data.remote_study_id
        self.rest_client = remote_genotype_data.rest_client

        super().__init__(remote_genotype_data)

        pheno_id = self.config.get("phenotype_data")
        if pheno_id:
            self._phenotype_data = RemotePhenotypeData(
                pheno_id,
                self.remote_study_id,
                self.rest_client,
            )

        self.is_remote = True

        self._person_set_collections = None
        self._person_set_collection_configs = None

    @cached_property
    def response_transformer(self) -> ResponseTransformer:
        return ResponseTransformer(self)

    @property
    def is_group(self) -> bool:
        return self.remote_genotype_data.is_group

    @property
    def person_set_collections(self) -> dict[str, PersonSetCollection]:
        return self.remote_genotype_data.person_set_collections

    @property
    def config_columns(self) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            self.config.genotype_browser.columns)

    @property
    def families(self) -> FamiliesData:
        return self.remote_genotype_data._families  # noqa: SLF001

    @property
    def parents(self) -> set[str]:
        return self.remote_genotype_data.parents

    @property
    def name(self) -> str:
        return self.remote_genotype_data.name

    def get_studies_ids(self, *, leaves: bool = True) -> list[str]:
        return self.remote_genotype_data.get_studies_ids(leaves=leaves)

    def query_variants_wdae_streaming(  # pylint: disable=arguments-differ
        self, kwargs: dict[str, Any],
        sources: list[dict[str, Any]],
        *,
        max_variants_count: int = 10000,
        max_variants_message: bool = False,  # noqa: ARG002
    ) -> Generator[list, None, None]:
        study_filters = kwargs.get("study_filters")
        person_set_collection_id = \
            kwargs.get("personSetCollection", {}).get("id")

        if study_filters is not None:
            del kwargs["study_filters"]
        if kwargs.get("allowed_studies"):
            del kwargs["allowed_studies"]

        kwargs["datasetId"] = self.remote_study_id
        kwargs["maxVariantsCount"] = max_variants_count
        new_sources = []
        for query_s in QUERY_SOURCES:
            if not any(query_s["source"] == s["source"] for s in sources):
                new_sources.append(query_s)  # noqa: PERF401
        sources.extend(new_sources)
        kwargs["sources"] = sources

        fam_id_idx = -1
        for idx, source in enumerate(sources):
            if source["source"] == "family":
                fam_id_idx = idx
                break

        assert fam_id_idx >= 0, fam_id_idx

        response = self.rest_client.post_query_variants(
            kwargs, reduce_alleles=False,
        )

        for source in sources:
            if "format" in source:
                del source["format"]

        def get_source(col: dict[str, Any]) -> Any:
            res = col["source"]
            if "role" in col:
                res = f"{res}.{col['role']}"
            return res

        for variant in response:
            fam_id = variant[fam_id_idx][0]
            family = self.families[fam_id]
            fv = RemoteFamilyVariant(
                variant, family, list(map(get_source, sources)))
            # pylint: disable=protected-access
            row_variant = self.response_transformer.build_variant_row(
                fv, sources, person_set_collection=person_set_collection_id)

            yield row_variant

    def get_person_set_collection(
        self, person_set_collection_id: str,
    ) -> PersonSetCollection | None:
        return self.remote_genotype_data.get_person_set_collection(
            person_set_collection_id,
        )

    def _init_pheno(self, *_, **__) -> None:
        # This method is not necessary for remote studies, as the phenotype
        # data is already initialized in the constructor.
        pass
