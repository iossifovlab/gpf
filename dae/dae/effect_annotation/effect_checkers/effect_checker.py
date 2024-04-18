import abc
from typing import Optional

from dae.effect_annotation.annotation_request import AnnotationRequest
from dae.effect_annotation.effect import AnnotationEffect


class EffectChecker(abc.ABC):

    @abc.abstractmethod
    def get_effect(
        self, request: AnnotationRequest,
    ) -> Optional[AnnotationEffect]:
        """Return an annotation effect or None."""
