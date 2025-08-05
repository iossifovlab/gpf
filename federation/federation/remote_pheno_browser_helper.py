import logging
from abc import abstractmethod
from collections.abc import Generator
from typing import Any

from gpf_instance.extension import GPFTool
from pheno_browser_api.pheno_browser_helper import BasePhenoBrowserHelper
from studies.study_wrapper import WDAEAbstractStudy

from federation.remote_study_wrapper import RemoteWDAEStudy
from rest_client.rest_client import RESTClient

logger = logging.getLogger(__name__)


class CountError(Exception):
    pass


class RemotePhenoBrowserHelper(BasePhenoBrowserHelper):
    """Base class for pheno browser helpers."""
    def __init__(self, rest_client: RESTClient, dataset_id: str) -> None:
        super().__init__()
        self.rest_client = rest_client
        self.dataset_id = dataset_id

    @staticmethod
    def make_tool(study: WDAEAbstractStudy) -> GPFTool | None:
        if not isinstance(study, RemoteWDAEStudy):
            return None

        return RemotePhenoBrowserHelper(
            study.rest_client,
            study.remote_study_id,
        )

    def get_instruments(self) -> list[str]:
        return self.rest_client.get_instruments(self.dataset_id)

    def get_measures_info(self) -> dict[str, Any]:
        return self.rest_client.get_browser_measures_info(self.dataset_id)

    def get_measure_description(self, measure_id: str) -> dict[str, Any]:
        return self.rest_client.get_measure_description(
            self.dataset_id,
            measure_id,
        )

    @abstractmethod
    def search_measures(
        self,
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Search measures."""

    @abstractmethod
    def get_measure_ids(
        self,
        data: dict[str, Any],
    ) -> Generator[str, None, None]:
        """Get measure ids."""

    @abstractmethod
    def count_measure_ids(
        self,
        data: dict[str, Any],
    ) -> int:
        """Get measure ids."""

    @abstractmethod
    def get_count(self, data: dict[str, Any]) -> int:
        """Return measure count for request."""

    @abstractmethod
    def get_image(self, image_path: str) -> tuple[bytes, str]:
        """Get image by path."""
