import json
import logging
from collections.abc import Generator, Iterable
from typing import Any, cast

from dae.pedigrees.families_data import FamiliesData
from dae.variants.variant import SummaryVariant
from studies.study_wrapper import (
    QueryTransformerProtocol,
    ResponseTransformerProtocol,
    WDAEAbstractStudy,
)

from federation.remote_phenotype_data import RemotePhenotypeData
from federation.remote_study import RemoteGenotypeData
from federation.utils import prefix_remote_identifier
from rest_client.rest_client import RESTClient

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
        self.children = [self]
        super().__init__(remote_genotype_data, remote_phenotype_data)
        self._families: FamiliesData | None = None

        self.remote_study_id = remote_study_id
        self.rest_client = rest_client
        self._study_id = prefix_remote_identifier(
            self.remote_study_id,
            self.rest_client,
        )

        self.query_transformer = None
        self.response_transformer = None
        self._description = ""

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

    @property
    def description(self) -> str | None:
        if self._description == "":
            self._description = self.rest_client.get_dataset_description(
                self.remote_study_id,
            )["description"]
        return self._description

    @description.setter
    def description(self, input_text: str) -> None:  # noqa: ARG002
        return

    def query_variants_wdae(
        self, kwargs: dict[str, Any],
        sources: list[dict[str, Any]],
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        *,
        max_variants_count: int | None = 10000,
        max_variants_message: bool = False,
    ) -> Generator[list | None, None, None]:
        raise NotImplementedError

    def handle_denovo_gene_sets(self, kwargs: dict[str, Any]) -> None:
        """Dirty fix for remote denovo gene sets."""
        if "geneSet" in kwargs:
            gene_set = kwargs["geneSet"]
            if gene_set["geneSetsCollection"] != "denovo":
                return
            for gst in gene_set["geneSetsTypes"]:
                if not gst["datasetId"].startswith(
                    self.rest_client.client_id,
                ):
                    raise ValueError(
                        "Invalid denovo gene set for remote study")
                gst["datasetId"] = gst["datasetId"].lstrip(
                    f"{self.rest_client.client_id}_")

    def handle_gene_sets(self, kwargs: dict[str, Any]) -> None:
        """Dirty fix for gene sets."""
        if "geneSet" in kwargs:
            gene_set = kwargs["geneSet"]
            if gene_set["geneSetsCollection"] == "denovo":
                return

            if not gene_set["geneSetsCollection"].startswith(
                self.rest_client.client_id,
            ):
                raise ValueError(
                    "Invalid denovo gene set for remote study")
            gene_set["geneSetsCollection"] = \
                gene_set["geneSetsCollection"].lstrip(
                    f"{self.rest_client.client_id}_")

    def handle_genomic_scores(self, kwargs: dict[str, Any]) -> None:
        """Dirty fix for remote genomic scores."""
        if "genomicScores" in kwargs:
            genomic_scores = kwargs["genomicScores"]
            for genomic_score in genomic_scores:
                if not genomic_score["score"].startswith(
                    self.rest_client.client_id,
                ):
                    raise ValueError(
                        "Invalid genomic score for remote study")
                genomic_score["score"] = genomic_score["score"].lstrip(
                    f"{self.rest_client.client_id}_")

    def query_variants_preview_wdae(
        self, kwargs: dict[str, Any],
        query_transformer: QueryTransformerProtocol,  # noqa: ARG002
        response_transformer: ResponseTransformerProtocol,  # noqa: ARG002
        *,
        max_variants_count: int | None = 10000,  # noqa: ARG002
    ) -> Generator[Any | None, None, None]:
        self.handle_denovo_gene_sets(kwargs)
        self.handle_gene_sets(kwargs)
        self.handle_genomic_scores(kwargs)

        kwargs["datasetId"] = self.remote_study_id
        if kwargs.get("allowed_studies") is not None:
            del kwargs["allowed_studies"]

        yield from self.rest_client.post_query_variants(
            kwargs,
        )

    def query_variants_download_wdae(
        self, kwargs: dict[str, Any],
        query_transformer: QueryTransformerProtocol,  # noqa: ARG002
        response_transformer: ResponseTransformerProtocol,  # noqa: ARG002
        *,
        max_variants_count: int | None = 10000,  # noqa: ARG002
    ) -> Generator[Any | None, None, None]:
        self.handle_denovo_gene_sets(kwargs)
        self.handle_gene_sets(kwargs)
        self.handle_genomic_scores(kwargs)

        kwargs["datasetId"] = self.remote_study_id
        if kwargs.get("allowed_studies") is not None:
            del kwargs["allowed_studies"]
        yield from self.rest_client.post_query_variants_download(
            kwargs,
        )

    def get_measures_json(
        self,
        used_types: list[str],  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            self.rest_client.get_measures_list(self.remote_study_id),
        )

    def build_genotype_data_description(self) -> dict[str, Any]:
        details = self.rest_client.get_dataset(self.remote_study_id)
        # Overwrite with prefixed versions
        details["id"] = self.study_id
        details["name"] = self.name
        return details

    def _init_pheno(self, *_, **__) -> None:
        # This method is not necessary for remote studies, as the phenotype
        # data is already initialized in the constructor.
        pass

    def get_gene_view_summary_variants(
        self,
        frequency_column: str,  # noqa: ARG002
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,  # noqa: ARG002
        **kwargs: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """Return gene browser summary variants."""

        variants = self._query_gene_view_summary_variants(
            query_transformer, **kwargs,
        )

        yield from variants

    def get_gene_view_summary_variants_download(
        self,
        frequency_column: str,  # noqa: ARG002
        query_transformer: QueryTransformerProtocol,  # noqa: ARG002
        response_transformer: ResponseTransformerProtocol,  # noqa: ARG002
        **kwargs: Any,
    ) -> Iterable:
        """Return gene browser summary variants for downloading."""
        kwargs["datasetId"] = self.remote_study_id
        data = {
            "queryData": json.dumps(kwargs),
        }
        return self.rest_client.post_gene_view_summary_variants_download(data)

    def _query_gene_view_summary_variants(
        self, query_transformer: QueryTransformerProtocol, **kwargs: Any,
    ) -> Generator[SummaryVariant, None, None]:
        kwargs["datasetId"] = self.remote_study_id

        study_filters = None
        if kwargs.get("allowed_studies") is not None:
            study_filters = kwargs.pop("allowed_studies")

        if kwargs.get("studyFilters"):
            if study_filters is not None:
                study_filters_param = kwargs.pop("studyFilters")
                study_filters = [
                    x for x in study_filters if x in study_filters_param]
            else:
                study_filters = kwargs.pop("studyFilters")
        kwargs["study_filters"] = study_filters

        kwargs = self._extract_pre_kwargs(query_transformer, kwargs)
        kwargs.pop("maxVariantsCount", None)
        return self.rest_client.post_gene_view_summary_variants(kwargs)

    def _extract_pre_kwargs(
            self, query_transformer: QueryTransformerProtocol,
            kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        pre_kwargs = {
            "personFilters": kwargs.pop("personFilters", None),
            "familyFilters": kwargs.pop("familyFilters", None),
            "personFiltersBeta": kwargs.pop("personFiltersBeta", None),
            "familyPhenoFilters": kwargs.pop("familyPhenoFilters", None),
            "personIds": kwargs.pop("personIds", None),
            "familyIds": kwargs.pop("familyIds", None),
        }
        pre_kwargs = {
            k: v for k, v in pre_kwargs.items() if v is not None
        }
        pre_kwargs = query_transformer.transform_kwargs(
            self, **pre_kwargs,
        )
        for key in ["person_ids", "family_ids"]:
            if pre_kwargs.get(key) is not None:
                kwargs[key] = pre_kwargs[key]
        return kwargs


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
