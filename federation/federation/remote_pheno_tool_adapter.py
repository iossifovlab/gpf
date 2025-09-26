from typing import Any

import pandas as pd
from gpf_instance.extension import GPFTool
from pheno_tool_api.adapter import PhenoToolAdapterBase
from studies.study_wrapper import WDAEAbstractStudy

from federation.remote_study_wrapper import (
    RemoteWDAEStudy,
    handle_denovo_gene_sets,
    handle_gene_sets,
    handle_genomic_scores,
)
from rest_client.rest_client import RESTClient


class RemotePhenoToolAdapter(PhenoToolAdapterBase):
    """Adapter for remote PhenoTool class."""

    def __init__(self, rest_client: RESTClient, dataset_id: str) -> None:
        self.rest_client = rest_client
        self.dataset_id = dataset_id

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        if not isinstance(study, RemoteWDAEStudy):
            return None

        return RemotePhenoToolAdapter(study.rest_client, study.remote_study_id)

    def calc_variants(
        self, query_data: dict[str, Any],
    ) -> dict[str, Any]:
        # pylint: disable=W0613
        query_data["datasetId"] = self.dataset_id
        handle_denovo_gene_sets(self.rest_client, query_data)
        handle_gene_sets(self.rest_client, query_data)
        handle_genomic_scores(self.rest_client, query_data)

        return self.rest_client.post_pheno_tool(query_data)  # type: ignore

    def produce_download_df(self, query_data: dict[str, Any]) -> pd.DataFrame:
        raise NotImplementedError
