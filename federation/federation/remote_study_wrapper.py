import logging
from collections.abc import Generator
from functools import cached_property
from typing import Any

from dae.pedigrees.families_data import FamiliesData
from studies.response_transformer import ResponseTransformer
from studies.study_wrapper import WDAEAbstractStudy

from federation.remote_phenotype_data import RemotePhenotypeData
from federation.remote_study import RemoteGenotypeData
from federation.remote_utils import build_remote_families
from federation.remote_variant import QUERY_SOURCES, RemoteFamilyVariant
from federation.rest_api_client import RESTClient

logger = logging.getLogger(__name__)


class RemoteWDAEStudy(WDAEAbstractStudy):
    """Wrapper class for remote (federation) studies."""

    def __init__(
        self,
        remote_study_id: str,
        rest_client: RESTClient,
        remote_genotype_data: RemoteGenotypeData | None = None,
        remote_phenotype_data: RemotePhenotypeData | None = None,
    ):
        super().__init__(remote_genotype_data, remote_phenotype_data)
        self._families: FamiliesData | None = None

        self.remote_study_id = remote_study_id
        self.rest_client = rest_client
        self._study_id = self.rest_client.prefix_remote_identifier(
            self.remote_study_id,
        )

        self.is_remote = True

    @property
    def study_id(self) -> str:
        return self._study_id

    def get_children_ids(
        self,
        *,
        leaves: bool = True,  # noqa: ARG002
    ) -> list[str]:
        """Return the list of children ids."""
        return [self._study_id]

    @cached_property
    def response_transformer(self) -> ResponseTransformer:
        return ResponseTransformer(self)

    @property
    def description(self) -> str | None:
        return ""

    @description.setter
    def description(self, input_text: str) -> None:  # noqa: ARG002
        return

    @property
    def families(self) -> FamiliesData:
        if self._families is None:
            self._families = build_remote_families(
                self.remote_study_id,
                self.rest_client,
            )
            self.genotype_data._families = self._families  # noqa: SLF001
        return self._families

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

    def _init_pheno(self, *_, **__) -> None:
        # This method is not necessary for remote studies, as the phenotype
        # data is already initialized in the constructor.
        pass


class RemoteWDAEStudyGroup(RemoteWDAEStudy):
    """Genotype data study wrapper class for WDAE."""

    def __init__(
        self,
        remote_study_id: str,
        rest_client: RESTClient,
        children: list[RemoteWDAEStudy],
        remote_genotype_data: RemoteGenotypeData | None = None,
        remote_phenotype_data: RemotePhenotypeData | None = None,
    ):
        super().__init__(
            remote_study_id,
            rest_client,
            remote_genotype_data,
            remote_phenotype_data,
        )
        self.children = children

    def get_children_ids(
        self,
        *,
        leaves: bool = True,  # noqa: ARG002
    ) -> list[str]:
        return [child.study_id for child in self.children]
