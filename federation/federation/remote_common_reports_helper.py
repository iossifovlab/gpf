import logging
from typing import Any

from common_reports_api.common_reports_helper import BaseCommonReportsHelper
from gpf_instance.extension import GPFTool
from studies.study_wrapper import WDAEAbstractStudy

from federation.remote_study_wrapper import RemoteWDAEStudy
from rest_client.rest_client import RESTClient

logger = logging.getLogger(__name__)


class RemoteCommonReportsHelper(BaseCommonReportsHelper):
    """Remote class for common reports helper."""
    def __init__(self, rest_client: RESTClient, dataset_id: str) -> None:
        super().__init__()
        self.rest_client = rest_client
        self.dataset_id = dataset_id

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        if not isinstance(study, RemoteWDAEStudy):
            return None

        return RemoteCommonReportsHelper(
            study.rest_client,
            study.remote_study_id,
        )

    def get_common_report(self) -> dict[str, Any] | None:
        return self.rest_client.get_common_report(self.dataset_id)

    def get_full_common_report(self) -> dict[str, Any] | None:
        return self.rest_client.get_common_report(self.dataset_id, full=True)

    def get_family_counter_list(
        self,
        group_name: str,
        counter_id: int,
    ) -> Any:
        return self.rest_client.get_family_counter_list(
            self.dataset_id,
            group_name,
            counter_id,
        )

    def get_family_counter_tsv(
        self,
        group_name: str,
        counter_id: int,
    ) -> list[str]:
        return list(self.rest_client.download_family_counter_tsv(
            self.dataset_id,
            group_name,
            counter_id,
        ))

    def get_family_data_tsv(
        self,
    ) -> list[str]:
        return list(self.rest_client.get_family_data_pedigree_file(
            self.dataset_id,
        ))

    def get_filtered_family_data_tsv(
        self,
        data: dict,
    ) -> list[str]:
        return list(self.rest_client.get_filtered_family_data_pedigree_file(
            self.dataset_id,
            data,
        ))
