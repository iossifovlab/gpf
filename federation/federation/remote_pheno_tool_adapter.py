from collections import Counter
from typing import Any

from dae.pheno_tool.pheno_tool_adapter import PhenoToolAdapterBase

from federation.rest_api_client import RESTClient


class RemotePhenoToolAdapter(PhenoToolAdapterBase):
    """Adapter for remote PhenoTool class."""

    def __init__(self, rest_client: RESTClient, dataset_id: str) -> None:
        self.rest_client = rest_client
        self.dataset_id = dataset_id

    def calc_variants(
        self, data: dict[str, Any], _effect_groups: list[str],
    ) -> dict[str, Any]:
        # pylint: disable=W0613
        data["datasetId"] = self.dataset_id
        return self.rest_client.post_pheno_tool(data)  # type: ignore

    def calc_by_effect(
        self, measure_id: str, effect: str, people_variants: Counter,
        person_ids: list[str] | None = None,
        family_ids: list[str] | None = None,
        normalize_by: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError
