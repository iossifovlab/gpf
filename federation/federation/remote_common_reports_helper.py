import logging

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
