from abc import abstractmethod
from typing import Any

import docker

from dae.annotation.annotation_config import AnnotatorInfo
from dae.annotation.annotation_pipeline import AnnotationPipeline, Annotator
from dae.annotation.annotator_base import AnnotatorBase, AttributeDesc


class DockerAnnotator(AnnotatorBase):
    """Base class for annotators that use docker containers."""
    def __init__(
        self, pipeline: AnnotationPipeline | None,
        info: AnnotatorInfo,
    ):
        """
        Base class for annotators that use the python Docker SDK.

        Creates a docker client to use for annotation and provides
        overridable methods to customize how the docker client,
        images and containers are managed.
        """
        super().__init__(pipeline, info, self._attribute_type_descs())
        self.client = self._create_client()

    @staticmethod
    def _create_client() -> docker.DockerClient:
        return docker.from_env()

    def _prepare_client(self) -> None:
        """
        Initialize client so that the required images are available.

        By default will call _init_images
        """
        self._init_images()

    def _init_images(self) -> None:
        """
        Initialize images on the docker client.

        Default implementation does nothing.
        """
        return

    @abstractmethod
    def run(self, **kwargs: Any) -> None:
        raise NotImplementedError

    def open(self) -> Annotator:
        self._prepare_client()
        return super().open()

    @abstractmethod
    def _attribute_type_descs(self) -> dict[str, AttributeDesc]:
        raise NotImplementedError
